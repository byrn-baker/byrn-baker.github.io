---
title: Nautobot Workshop Blog Series - Part 13 - Python Coding Fundamentals
date: 2025-09-12 0:00:00
categories: [Nautobot, Ansible, Automation]
tags: [NetworkAutomation, NetworkSourceOfTruth, nautobot, AutomationPlatform, NautobotTutorials]
image:
  path: /assets/img/nautobot_workshop/light_title_image-50.webp
---

# Python Coding Fundamentals for Nautobot Jobs
Taking a step back because I think we need more information on the Python fundamentals that Nautobot Jobs use. During a recent interview, I was asked general Python questions about testing, classes, functions, and object-oriented programming (OOP). As a Python beginner who’s never read a Python book, I've relied solely on GitHub examples to build my automation scripts, which led to shaky answers. This experience prompted me to research these concepts to better understand the terminology and improve my skills. In this blog post, I’ll clarify these fundamentals and demonstrate how to create and test Nautobot Jobs using Nautobot standards, drawing on patterns from [Nautobot’s test suite](https://github.com/nautobot/nautobot/blob/develop/nautobot/extras/tests/test_jobs.py) to ensure accurate testing.

Let’s define the interview topics:
- **Functions**: Reusable blocks of code that perform a specific task, taking inputs and producing outputs.
- **Classes**: Templates for creating objects that combine data (attributes) and behavior (methods).
- **Object-Oriented Programming (OOP)**: A programming approach that organizes code around objects, which are instances of classes. OOP uses principles like:
  - **Encapsulation**: Keeping data and methods that operate on that data together within a class, protecting the data from external interference.
  - **Inheritance**: Allowing a class to inherit properties and methods from another class, promoting code reuse.
  - **Polymorphism**: Enabling different classes to share a common interface, so methods can behave differently based on the object calling them.
- **Testing**: Writing code to verify that a program works as expected, often through automated tests to catch errors early.

Below, we’ll explore these concepts in the context of writing and testing Nautobot Jobs, ensuring tests work in a standard environment.

## 1. Classes and Functions in Nautobot Jobs
**Functions**
Functions encapsulate reusable logic, ideal for tasks like querying data in Nautobot Jobs. Functions should use Django’s ORM efficiently and follow the name-based convention for models like Status and Tag.

### Nautobot Job Class Hierarchy
The following diagram shows how custom Jobs inherit from `nautobot.apps.jobs.Job`, with key attributes and methods:

```
nautobot.apps.jobs.Job
├── Attributes:
│   ├── job_result (for logging success/failure)
│   ├── logger (for logging messages)
│   └── Meta (name, description, read_only)
├── Methods:
│   ├── run() [abstract, must override]
│   └── log_success(), log_failure(), log_info()
│
├── DeviceReportJob
│   ├── Meta: name="Device Report", description="Generate a report of active devices", read_only=True
│   └── run(): Counts active devices
│
├── DeviceConfigValidator
│   ├── Meta: name="Validate Device Configurations", description="Check if devices have valid NTP configurations", read_only=True
│   ├── validate_config(device): Checks NTP servers in config_context
│   └── run(): Validates NTP configs for active devices
│
└── DeviceTagCheckerJob
    ├── Meta: name="Device Tag Checker", description="Check if all devices have the 'Critical' tag", read_only=True
    └── run(): Checks for 'Critical' tag on active devices
```

For example:

```python
def run(self):
      """Execute the job to count active devices."""
      active_status = Status.objects.get_for_model(Device).get(name="Active")
      devices = Device.objects.filter(status=active_status)
      self.logger.success(message=f"Found {devices.count()} active devices")
```
This function retrieves all active devices from Nautobot’s database as a queryset, making it reusable across Jobs for clean, focused code.

**Classes**
Nautobot Jobs are defined as classes inheriting from `nautobot.apps.jobs.Job`. This base class provides enhanced logging and result-tracking features. Jobs must implement the `run` method and use the `Meta` class for metadata.

Example of a simple Nautobot Job:

```python
from nautobot.apps.jobs import Job, register_jobs
from nautobot.dcim.models import Device
from nautobot.extras.models import Status

class DeviceReportJob(Job):
    """Generate a report of all active devices in Nautobot."""

    class Meta:
        name = "Device Report"
        description = "Generate a report of active devices"
        read_only = True

    def run(self):
        """Execute the job to count active devices."""
        active_status = Status.objects.get_for_model(Device).get(name="Active")
        devices = Device.objects.filter(status=active_status)
        self.logger.success(message=f"Found {devices.count()} active devices")

register_jobs(DeviceReportJob)
```

## 2. Object-Oriented Programming (OOP) in Nautobot Jobs
OOP organizes code around objects, leveraging encapsulation, inheritance, and polymorphism to create modular, maintainable Nautobot Jobs.

**Applying OOP Principles**
- Encapsulation: Grouping related logic (e.g., device validation) within a class to keep code organized.
- Inheritance: Jobs inherit from nautobot.apps.jobs.Job, accessing built-in methods like job_result.log_success.
- Polymorphism: Customizing the run method or adding helper methods to tailor Job behavior.

Here’s a Job that validates device configurations:
```python
# jobs/device_config_validator.py

from nautobot.apps.jobs import Job, register_jobs
from nautobot.dcim.models import Device
from nautobot.extras.models import Status


class DeviceConfigValidator(Job):
    """Validate NTP configurations for active devices in Nautobot."""

    class Meta:
        name = "Validate Device Configurations"
        description = "Check if devices have valid NTP configurations"
        read_only = True

    def validate_config(self, device):
        """Return True if device has NTP servers defined in its merged config context."""
        context = {}
        try:
            context = device.get_config_context() or {}
        except Exception as exc:
            self.logger.warning(f"Unable to retrieve config context for {device}: {exc}")
            return False

        ntp_servers = context.get("ntp_servers", [])
        return bool(ntp_servers)

    def run(self):
        """Execute the job to validate NTP configurations for active devices."""
        try:
            active_status = Status.objects.get_for_model(Device).get(name="Active")
        except Status.DoesNotExist:
            msg = "Status 'Active' not found"
            self.logger.failure(msg)
            raise RuntimeError(msg)

        devices = Device.objects.filter(status=active_status)

        valid = 0
        invalid = 0
        for device in devices:
            if self.validate_config(device):
                valid += 1
                self.logger.success(f"{device.name} has valid NTP config")
            else:
                invalid += 1
                self.logger.failure(f"{device.name} has invalid NTP config")

        result = f"Validated {devices.count()} devices: {valid} valid, {invalid} invalid"
        self.logger.info(result)
        return result


register_jobs(DeviceConfigValidator)
```
## 3. Test-Driven Development (TDD) for Nautobot Jobs
**Test-Driven Development (TDD)** ensures reliability by writing tests before code (or as your code), critical for Jobs interacting with network infrastructure. TDD is supported with pytest and pytest-django, and tests create living documentation by describing expected behavior. Nautobot’s test suite uses nautobot.apps.testing.TransactionTestCase and run_job_for_testing to test Jobs realistically, handling Celery task boundaries and Job registration.

**TDD Workflow**
1. **Write a failing test**: Define expected behavior in a test case.
2. **Write minimal code**: Implement just enough code to pass the test.
3. **Refactor**: Optimize code while ensuring tests pass.

**Documentation in TDD**
Tests act as living documentation by:
- **Clarifying Intent**: Tests describe what the code should do, serving as executable examples of functionality.
- **Maintaining Accuracy**: Unlike static documentation, tests are updated with code changes, ensuring they reflect current behavior.
- **Guiding Collaboration**: Tests help team members understand the Job’s purpose and behavior without digging through code.

Complement TDD with:
- **Docstrings**: Add clear docstrings to classes, methods, and functions to explain their purpose.
- **Comments**: Use inline comments for complex logic.
- **Job Metadata**: Use the Meta class’s description to document the Job’s purpose in the UI.

Here’s a Job that checks if devices have a specific tag, built with TDD and documented.

**Job Code**
Using our container environment, place the Job in `nautobot-docker-compose/jobs/device_tag_checker.py`:
```python
# jobs/device_tag_checker.py
from nautobot.apps.jobs import Job, register_jobs
from nautobot.dcim.models import Device
from nautobot.extras.models import Status, Tag

class DeviceTagCheckerJob(Job):
    class Meta:
        name = "Device Tag Checker"
        description = "Check if all devices have the 'Critical' tag"
        read_only = True

    def run(self):
        try:
            tag = Tag.objects.get(name="Critical")
        except Tag.DoesNotExist:
            msg = "Tag 'Critical' not found"
            self.logger.failure(msg)
            raise RuntimeError(msg)

        try:
            active_status = Status.objects.get_for_model(Device).get(name="Active")
        except Status.DoesNotExist:
            msg = "Status 'Active' not found"
            self.logger.failure(msg)
            raise RuntimeError(msg)

        missing_tag_count = Device.objects.filter(status=active_status).exclude(tags=tag).count()
        result = f"{missing_tag_count} device(s) missing the 'Critical' tag"
        self.logger.success(result)
        return result

register_jobs(DeviceTagCheckerJob)
```

**Test Code**
Nautobot jobs often encapsulate business logic: evaluating device inventory, setting tags, validating data, or integrating with external systems. Automated tests let you:
- Validate behavior for both happy-path and error scenarios
- Ensure database dependencies are set up properly
- Confidently refactor your job logic without breaking functionality

Make sure `jobs/tests/` are Python packages (add `__init__.py` files).

Nautobot 2.4 specifics you need to account for:
- Job logs are stored in a separate database alias: job_logs. Allow it in your test case’s databases attribute.
- JobResult status values use Celery task states (e.g., “SUCCESS”, “FAILURE”), not “completed/failed”.
- Creating a `Device` in Nautobot 2.x requires related objects: `LocationType`, `Location`, `Manufacturer`, `DeviceType`, `Role`, and a `Status` that’s mapped to the `Device` and `Location` content types.

Here’s a complete test module that covers success, empty inventory, and error cases:

Place the test in `nautobot-docker-compose/jobs/tests/test_device_tag_checker.py`:
```python
# jobs/tests/test_device_tag_job.py

from django.contrib.contenttypes.models import ContentType

from nautobot.apps.testing import TransactionTestCase, run_job_for_testing
from nautobot.dcim.models import (
    Device,
    Location,
    LocationType,
    Manufacturer,
    DeviceType,
)
from nautobot.extras.models import Status, Tag, Job, JobLogEntry, Role

# Ensure the job module is imported so register_jobs() is executed
from jobs.device_tag_checker import DeviceTagCheckerJob  # noqa: F401


class DeviceTagCheckerJobTestCase(TransactionTestCase):
    # Allow both the default DB and the job_logs DB used for JobLogEntry
    databases = ("default", "job_logs")

    def setUp(self):
        super().setUp()

        # Status used by Devices and Locations
        self.active_status, _ = Status.objects.get_or_create(name="Active")
        ct_device = ContentType.objects.get_for_model(Device)
        ct_location = ContentType.objects.get_for_model(Location)
        self.active_status.content_types.add(ct_device, ct_location)

        # Tag
        self.tag, _ = Tag.objects.get_or_create(name="Critical")

        # Location hierarchy (minimal)
        self.location_type, _ = LocationType.objects.get_or_create(name="Site")
        self.location = Location.objects.create(
            name="Test-Site",
            location_type=self.location_type,
            status=self.active_status,
        )

        # Device Type prerequisites
        self.manufacturer = Manufacturer.objects.create(name="Acme")
        self.device_type = DeviceType.objects.create(
            manufacturer=self.manufacturer,
            model="Router-1",
        )

        # Role for Devices
        self.role, _ = Role.objects.get_or_create(name="Network")
        self.role.content_types.add(ct_device)

    def _create_device(self, name):
        return Device.objects.create(
            name=name,
            status=self.active_status,
            location=self.location,
            role=self.role,
            device_type=self.device_type,
        )

    def _get_job_model(self):
        # module_name should match the filename jobs/device_tag_checker.py
        return Job.objects.get(
            job_class_name="DeviceTagCheckerJob",
            module_name="device_tag_checker",
        )

    def test_device_tag_checker(self):
        """Test DeviceTagCheckerJob identifies devices missing the 'Critical' tag."""
        device1 = self._create_device("device1")
        device1.tags.add(self.tag)
        self._create_device("device2")  # no tag

        job = self._get_job_model()
        job_result = run_job_for_testing(job)

        # Status uses Celery states in Nautobot 2.4
        self.assertEqual(job_result.status, "SUCCESS")
        self.assertEqual(job_result.result, "1 device(s) missing the 'Critical' tag")

        expected_message = "1 device(s) missing the 'Critical' tag"
        log_entries = JobLogEntry.objects.filter(job_result=job_result, message=expected_message)
        self.assertTrue(log_entries.exists(), "Expected success log entry not found.")
        self.assertEqual(log_entries.first().log_level, "success")

    def test_device_tag_checker_no_devices(self):
        """Test DeviceTagCheckerJob when no devices exist."""
        job = self._get_job_model()
        job_result = run_job_for_testing(job)

        self.assertEqual(job_result.status, "SUCCESS")
        self.assertEqual(job_result.result, "0 device(s) missing the 'Critical' tag")

        expected_message = "0 device(s) missing the 'Critical' tag"
        log_entries = JobLogEntry.objects.filter(job_result=job_result, message=expected_message)
        self.assertTrue(log_entries.exists(), "Expected success log entry not found.")
        self.assertEqual(log_entries.first().log_level, "success")

    def test_device_tag_checker_missing_tag(self):
        """Test DeviceTagCheckerJob when the 'Critical' tag does not exist."""
        Tag.objects.filter(name="Critical").delete()

        job = self._get_job_model()
        job_result = run_job_for_testing(job)

        self.assertEqual(job_result.status, "FAILURE")

        expected_message = "Tag 'Critical' not found"
        log_entries = JobLogEntry.objects.filter(job_result=job_result, message=expected_message)
        self.assertTrue(log_entries.exists(), "Expected failure log entry not found.")
        self.assertEqual(log_entries.first().log_level, "failure")
```

**Key points**:
- databases = ("default", "job_logs") is required to allow writing to the job logs database during tests.
- Using run_job_for_testing(job) executes the job synchronously in the test environment.
- We import the job module at the top (from jobs.device_tag_checker import DeviceTagCheckerJob) so that register_jobs() runs and a Job row exists when we query it.

**Testing Instructions**
Inside your Nautobot container run the following:
```bash
nautobot-server test jobs/tests
```

You should see a similar output from the test
```bash
nautobot@605711153a37:~$ nautobot-server test jobs/tests
Implicitly excluding tests tagged 'integration'
Implicitly excluding tests tagged 'migration_test'
Found 3 test(s).
Creating test database for alias 'default'...

>>> Checking whether any Interface or VMInterface has IPs with differing VRFs...
    ... completed (elapsed time: 0.0 seconds)
>>> Verifying all Prefix.broadcast values...
    ... completed (elapsed time: 0.0 seconds)
>>> Setting Prefix.version and IPAddress.version values...
    ... completed (elapsed time: 0.0 seconds)
>>> Processing VRFs...
    ... completed (elapsed time: 0.0 seconds)
>>> Processing IPAddresses...
    >>> Reparenting individual IPAddresses to a close-enough parent Prefix...
        ... completed (elapsed time: 0.0 seconds)
    >>> Reparenting orphaned IPAddresses by creating new Prefixes as needed...
        ... completed (elapsed time: 0.0 seconds)
    ... completed (elapsed time: 0.0 seconds)
>>> Processing duplicate Prefixes...
    ... completed (elapsed time: 0.0 seconds)
>>> Reparenting Prefixes...
    ... completed (elapsed time: 0.0 seconds)
>>> Copying VRFs to cleanup Namespaces as needed...
    ... completed (elapsed time: 0.0 seconds)
>>> Processing Interfaces and VM Interfaces...
    ... completed (elapsed time: 0.0 seconds)
>>> Processing VRF to Prefix many-to-many...
    ... completed (elapsed time: 0.0 seconds)

    Checking for duplicate records ...

    Checking for duplicate records ...

    Checking for duplicate records ...

    Checking for duplicate records ...

>>> Finding and removing any invalid or dangling Note objects ...


>>> Removal completed. 

/usr/local/lib/python3.12/site-packages/napalm/__init__.py:1: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  import pkg_resources
System check identified no issues (0 silenced).

.nautobot_bgp_models: Unable to find status: Available .. SKIPPING
nautobot_bgp_models: Unable to find status: Planned .. SKIPPING
nautobot_bgp_models: Unable to find status: Planned .. SKIPPING
nautobot_bgp_models: Unable to find status: Deprovisioning .. SKIPPING
nautobot_bgp_models: Unable to find status: Offline .. SKIPPING
nautobot_bgp_models: Unable to find status: Planned .. SKIPPING
nautobot_bgp_models: Unable to find status: Provisioning .. SKIPPING

.nautobot_bgp_models: Unable to find status: Available .. SKIPPING
nautobot_bgp_models: Unable to find status: Planned .. SKIPPING
nautobot_bgp_models: Unable to find status: Planned .. SKIPPING
nautobot_bgp_models: Unable to find status: Deprovisioning .. SKIPPING
nautobot_bgp_models: Unable to find status: Offline .. SKIPPING
nautobot_bgp_models: Unable to find status: Planned .. SKIPPING
nautobot_bgp_models: Unable to find status: Provisioning .. SKIPPING

.nautobot_bgp_models: Unable to find status: Available .. SKIPPING
nautobot_bgp_models: Unable to find status: Planned .. SKIPPING
nautobot_bgp_models: Unable to find status: Planned .. SKIPPING
nautobot_bgp_models: Unable to find status: Deprovisioning .. SKIPPING
nautobot_bgp_models: Unable to find status: Offline .. SKIPPING
nautobot_bgp_models: Unable to find status: Planned .. SKIPPING
nautobot_bgp_models: Unable to find status: Provisioning .. SKIPPING

----------------------------------------------------------------------
Ran 3 tests in 10.972s

OK
Destroying test database for alias 'default'...
```

**If you see**:
- “One of the test labels is a path to a file … not supported”: switch to a dotted path.
- “DatabaseOperationForbidden … job_logs”: add "job_logs" to your test case’s databases.
- “Job matching query does not exist”: 
make sure your job module is imported in the test (or JOBS_ROOT is configured).

## Common Pitfalls and Fixes
- **Job not discovered**: Ensure jobs/ is on PYTHONPATH (usually your project root), JOBS_ROOT points to jobs/, or import the job in your test.
- **Device creation errors**: Provide location, role, device_type, and a status that is associated with the Device content type.
- **Status string mismatches**: Expect “SUCCESS”/“FAILURE” (Celery states) in Nautobot 2.4, not “completed/failed”.
- **Too-strict log assertions**: Nautobot may write multiple log lines; assert the presence of the expected message rather than an exact count.

## Best Practices for Nautobot Jobs
- **Modularize Code**: Use functions for simple tasks and classes for complex logic.
- **Apply OOP**: Leverage encapsulation, inheritance, and polymorphism for maintainable code.
- **Adopt TDD**: Write tests first to ensure reliability.
- **Document Thoroughly**: Use docstrings, comments, and Meta attributes to explain code purpose.
- **Use Nautobot APIs**: Query models like Device.objects and use get_for_model for dynamic status handling with name.
- **Test with TransactionTestCase**: Use run_job_for_testing for realistic Job execution.
- **Log Effectively**: Use job_result.log_success, log_failure, and log_info for clear UI feedback.

# Conclusion
The interview questions about Python fundamentals exposed gaps in my knowledge as a beginner, but researching classes, functions, OOP, TDD, and documentation has clarified these concepts and improved my approach to Nautobot Jobs. By aligning with Nautobot standards, emphasizing documentation, you can create powerful, reliable, and well-documented automation scripts. Whether you’re new to Python or refining your skills, these principles, combined with Nautobot’s GitHub examples, will help you build effective Jobs for network automation.

Explore the [Nautobot documentation](https://archive.docs.nautobot.com/projects/core/en/stable/) and [GitHub repository](https://github.com/nautobot/nautobot) for more examples.

Full code as always is in my [Github Repository](https://github.com/byrn-baker/Nautobot-Workshop).