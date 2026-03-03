document.getElementById("videoInput").addEventListener("change", function(event){
    var preview = document.getElementById("videoPreview")

    if(event.target.files[0]){
        var fileURL = URL.createObjectURL(event.target.files[0]);
        preview.src = fileURL;
        preview.style.display = "block"
    }
    else{
        preview.src = ""
        preview.style.display = "none"
    }
    
});

document.getElementById("audioInput").addEventListener("change", function(event){
    var preview = document.getElementById("audioPreview")

    if(event.target.files[0]){
        var fileURL = URL.createObjectURL(event.target.files[0]);
        preview.src = fileURL;
        preview.style.display = "block"
    }
    else{
        preview.src = ""
        preview.style.display = "none"
    }
    
});

var encodeButton = document.getElementById('Encodebtn');
var decodeButton = document.getElementById('Decodebtn');

var encodeSection = document.getElementById('encode');
var decodeSection = document.getElementById('decode');

encodeSection.style.display = 'block';
decodeSection.style.display = 'none';

encodeButton.addEventListener('click',function(){
    encodeSection.style.display = 'block';
    decodeSection.style.display = 'none';   
})

decodeButton.addEventListener('click',function(){
    encodeSection.style.display = 'none';
    decodeSection.style.display = 'block';   
})

const encodedForm = document.getElementById("encode_content")
const progressBar = document.getElementById("progressBar")
const progressText = document.getElementById("progressText")

encodedForm.addEventListener("submit", async function(e) {
    e.preventDefault();

    progressBar.style.display = "block";
    progressBar.value = 0;

    let formData = new FormData(encodedForm);
    fetch("/encode",{
        method: "POST",
        body: formData
    });

    progressText.innerText = "Encoding";

    const interval = setInterval( async() =>{
        const prog = await fetch("/progress")
        const data = await prog.json();

        progressBar.value = data.progress;
        progressText.innerText = data.progress + " %";
        if (data.progress >= 100){
            clearInterval(interval);
            window.location.href = "/video";
        }
}, 300)

})

const decodeForm = document.getElementById("decode_content")
const decprogressBar = document.getElementById("decprogressBar")
const decprogressText = document.getElementById("decprogressText")

decodeForm.addEventListener("submit", async function(e) {
    e.preventDefault();

    decprogressBar.style.display = "block";
    decprogressBar.value = 0;

    let formData = new FormData(decodeForm);
    fetch("/decode",{
        method: "POST",
        body: formData
    });

    decprogressText.innerText = "Decoding";

    const interval = setInterval( async() =>{
        const decprog = await fetch("/decode_progress")
        const decdata = await decprog.json();

        decprogressBar.value = decdata.progress;
        decprogressText.innerText = decdata.progress + " %";
        if (decdata.progress >= 100){
            clearInterval(interval);
            window.location.href = "/decoded";
        }
}, 300);

});

