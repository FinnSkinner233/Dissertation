document.getElementById("videoInput").addEventListener("change", function(event){
    var preview = document.getElementById("videoPreview")

    if(event.target.files[0]){
        var URL = URL.createObjectURL(file);
        preview.src = URL;
        preview.style.display = "block"
    }
    else{
        preview.src = ""
        preview.style.display = "none"
    }
    
});