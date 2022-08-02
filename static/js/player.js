function play_url(video_id, url) {
    var video_src = url;

    const create = () => {
        const video = document.getElementById(video_id);

        if (video.canPlayType('application/vnd.apple.mpegurl')) {
            // since it's not possible to detect timeout errors in iOS,
            // wait for the playlist to be available before starting the stream
            video.src = video_src;
        } else {
            const hls = new Hls({
                progressive: true,
            });

            hls.on(Hls.Events.ERROR, (evt, data) => {
                if (data.fatal) {
                    hls.destroy();

                    setTimeout(create, 2000);
                }
            });

            hls.loadSource(video_src);
            hls.attachMedia(video);

            video.play();
        }
    };
    window.addEventListener('DOMContentLoaded', create);
}