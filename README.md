# Motion JPEG Streaming

> Fork from [CamStream-V3](https://github.com/avramit/CamStream-V3)

用来通过HTTP直接在浏览器中播放摄像头（或视频文件）。

> 其实就是用OpenCV获取摄像头或视频文件的每一帧画面，如果需要的话对画面进行加工，比如添加水印等，然后发送这一帧画面给浏览器，不断的重复这个过程。

对原代码的改进：增加了播放视频文件的支持，包括帧速的控制

**安装**：

```Bash
$ brew install opencv
```

**运行**：

摄像头

```Bash
$ python3 main.py
```

> Ctrl + C 结束

文件

```Bash
$ python3 main.py -f=movie.mp4
```

浏览器访问：

```
http://127.0.0.1:5000/
```

**效果**：


![screenshot](https://github.com/SixQuant/CamStream-V3/blob/master/screenshot.png?raw=true)
