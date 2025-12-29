---
title: Building a RTMP Video Streamer with NGINX
date: 2024-04-17 12:00:00 -500
categories: [100DaysOfHomeLab]
tags: [nginx,rtmp,100DaysOfHomeLab]

image:
  path: /assets/img/headers/nginx-streaming-banner.webp
---

## Building NGINX and RTMP module
I am using an ubuntu 22.04 VM for this build along with this Github [repo](https://github.com/sergey-dryabzhinsky/nginx-rtmp-module.git) for the RTMP module.

First clone the repo locally
```bash
git clone https://github.com/sergey-dryabzhinsky/nginx-rtmp-module.git
```

Install a couple of dependencies
```bash
sudo apt-get install build-essential libpcre3 libpcre3-dev libssl-dev zlib1g zlib1g-dev
```

Download the latest version of NGINX
```bash
wget https://nginx.org/download/nginx-1.25.5.tar.gz
tar -xf nginx-1.25.5.tar.gz
cd nginx-1.25.5/
```

Compile NGINX with the RTMP module from the Github repo
```bash
./configure --with-http_ssl_module --add-module=../nginx-rtmp-module
make -j 1
sudo make install
```

## Setting up NGINX
nginx should now be install in ```/usr/local/nginx/conf/nginx.conf```. You can move the nginx.conf to a new file or just edit the existing one. I'll leave that up to you.

In the nginx.conf lets add our rtmp configuration

```
worker_processes auto;
events {
    worker_connections 1024;
}

# RTMP SETTINGS
rtmp {
    server {
        listen 1935;
        chunk_size 4000;

        application show {
            live on;
            interleave on;
            hls on;
            hls_path /nginx/hls/;
            hls_fragment 3s;
            hls_playlist_length 60;
            # disable consuming the stream frm nginx as rtmp
            deny play all;
            dash on;
            dash_path /nginx/dash;
            dash_fragment 3s;
            #pull rtmp://tv2.example.com:443/root/new name=tv2 static;
        }
    }
}
```

We also need to add some configurations for the HTTP server as well and that will just go below rtmp in the nginx.conf file

```
http {
    sendfile off;
    tcp_nopush on;
    directio 512;
    default_type application/octet-stream;

    # Access log - All requests to your server
    access_log /var/log/nginx/access.log;
    # Error log - Any errors experienced by your server
    error_log /var/log/nginx/error.log;

    server {
        listen 80;

        location /hls/ {
            proxy_cache_valid 200 30s;

            types {
               application/dash+xml mpd;
               application/vnd.apple.mpegurl m3u8;
               video/mp2t ts;
               text/html html;
            }

            root /nginx/;
        }
        location /dash/ {
            proxy_cache_valid 200 30s;

            types {
               application/dash+xml mpd;
               application/vnd.apple.mpegurl m3u8;
               video/mp2t ts;
               text/html html;
            }

            root /nginx/;
        }
    }
}
```
Notice that we refenced a folder in both configurations, we need to ensure that those folder exist before starting nginx for the first time.

```bash
$ sudo mkdir /nginx
$ sudo mkdir /nginx/hls
$ sudo mkdir /nginx/dash
```

Change the owner of these folder to www-data
```bash
$ sudo chown -R www-data:www-data /nginx
```

We should now see that www-data is owner of these folders that were just created
```bash
$ ls -al /nginx/
total 12
drwxr-xr-x  3 www-data www-data 4096 Apr 17 16:39 .
drwxr-xr-x 20 root     root     4096 Apr 17 16:39 ..
drwxr-xr-x  2 www-data www-data 4096 Apr 17 16:39 hls
```

Lets run this in the foreground with daemon off to see if our configuration is working
```bash
$ sudo /usr/local/nginx/sbin/nginx -g 'daemon off;'
```

## Setting up and using FFMPEG
I am going to use [blenders big buck bunny](https://download.blender.org/peach/bigbuckbunny_movies/) video as our streaming example, so that you can easily replicate this yourself without OBS is a webcam.

we need to also install ffmpeg, and use it to stream something to our nginx rtmp server 
```bash
$ sudo apt install ffmpeg
$ ffmpeg -stream_loop -1 -re -i bbb_sunflower_1080p_60fps_normal.mp4 -vcodec copy -loop -1 -c:a aac -b:a 160k -ar 44100 -strict -2 -f flv rtmp://localhost/show/test
```

This will loop the stream until you stop it. You should be able to connect to the hosts IP address with ```rtmp://example.com/show/test```

 you can use VLC to connect to the server and see the stream.
<img src="/assets/img/vlc-open-media.webp" alt="">

If you use  ```http://example.com/hls/test.m3u8```  you should see the player load in the middle of the stream
<img src="/assets/img/vlc-bbb-test.webp" alt="">

You can keep HLS running and open a new window and load DASH with this file  ```http://example.com/dash/test.mpd```  at the same time and see both formats playing side by side like this 
<img src="/assets/img/test-bbb-both-formats.webp" alt="">

So there you have a streaming server in no time that can be self hosted. There is more to look at here, but I'll save that for another post as I build this concept out.