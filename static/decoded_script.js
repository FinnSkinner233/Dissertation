function loadAudioMetrics(){
    fetch('/metrics')
        .then(response => response.json())
        .then(data=> {
            if(data.audio_metrics !== undefined){
                document.getElementById("audio_metric_display").innerHTML =`
                <p>Hash of audio before encoding: ${data.audio_metrics.encoded_hash}</p>
                <p>Hash of audio after encoding: ${data.audio_metrics.decode_hash}</p>
                <p>Pearsons Correlation Coefficient: ${data.audio_metrics.correlation_coefficent}</p>
                <p>Bit rate error: ${data.audio_metrics.bit_rate_error}
                `;
            }else{
                setTimeout(loadAudioMetrics, 1000)
            }
    })
}

loadAudioMetrics()
