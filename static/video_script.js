function loadMetrics(){
    fetch('/quality_metrics')
        .then(response => response.json())
        .then(data=> {
            if (data.BPP !== undefined){
                document.getElementById("quality_metrics_display").innerHTML = `
                <p>Bits per pixles (payload capacity): ${data.BPP}</p>
                <p>Mean Squared Error: ${data.MSE}</p>
                <p>Peak Signal to Noise Ratio: ${data.PSNR}</p>
                <p>Structured Similarity Index Measurement: ${data.SSIM}</p>
                <p>Original video size: ${data.video_size} bytes</p>
                <p>Encoded video size: ${data.encoded_video_size} bytes</p>
                <p>Video size difference: ${data.size_difference} bytes</p>
                <p>Video size percentage difference: ${data.percent_size_diff} %</p>
                `;
            }else{
                setTimeout(loadMetrics, 1000)
            }
        })
}

function loadAudiohashes(){
    fetch('/hashes')
        .then(respsonse => respsonse.json())
        .then(data=> {
            if(data.audio_hashes !== undefined){
                document.getElementById("audio_hash_display").innerHTML =`
                <p>Hash of audio before encoding: ${data.audio_hashes.encoded_hash}</p>
                `;
            }else{
                setTimeout(loadAudiohashes, 1000)
            }
    })
}

loadMetrics();
loadAudiohashes()