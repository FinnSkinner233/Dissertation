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