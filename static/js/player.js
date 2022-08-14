function play_url(video_id, url) {
    var video_src = url;

    var video = document.getElementById(video_id);
    if (video.canPlayType('application/vnd.apple.mpegurl')) {
		video.src = video_src;

	} else if (Hls.isSupported()) {
		var hls = new Hls();
		hls.loadSource(video_src);
		hls.attachMedia(video);
	}
}