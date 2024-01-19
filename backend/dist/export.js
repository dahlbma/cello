var lines = ''
var sToken = ''
let xhr = new XMLHttpRequest();
let token_url = 'https://esox3.scilifelab.se/vialdb/initiateSdfDownload';
var numberOfElements = 0;

document.getElementById('inputfile')
    .addEventListener('change', function () {
	
	let fr = new FileReader();
	fr.onload = function () {
	    lines = fr.result.split(/[\r\n]+/g);
	    document.getElementById('output')
	    numberOfElements = lines.length;
	    xhr.open("GET", token_url, true);

	    // function execute after request is successful 
	    xhr.onreadystatechange = function () {
		if (this.readyState == 4 && this.status == 200) {
		    sToken = this.responseText;

		    var sdfileElement = document.getElementById('sdfile');
		    // Update the href attribute
		    sdfileElement.href = "https://esox3.scilifelab.se/vialdb/dist/export/" + sToken + "/export.sdf";
		    sdfileElement.textContent = '';


		    var errorDiv = document.getElementById('errorDiv');
		    // Set the display property to 'none' to make it invisible
		    errorDiv.style.display = 'none';


		    progress();
		}
	    }
	    // Sending our request 
	    xhr.send();
	}
	fr.readAsText(this.files[0]);
    })


// https://esox3.scilifelab.se/vialdb/initiateSdfDownload
// https://esox3.scilifelab.se/vialdb/addMolfileToSdf/977775/test

var i = 0;
var iChunks = 20;
var iCount = 0;
var errorString = 'These Ids have no molfile:\n';
function progress() {
    if (i == 0) {
	i = 1;
	var elem = document.getElementById("progressBar");
	var width = 1;
	var startIndex = 0;
        var endIndex = Math.min(startIndex + iChunks, lines.length);
	
	function frame() {
            var batch = lines.slice(startIndex, endIndex).join(',');

	    url = 'https://esox3.scilifelab.se/vialdb/addMolfileToSdf/' + sToken + '/' + batch
	    fetch(url, { method: 'GET' })
		.then(Result => Result.json())
		.then(response => {
		    var len = Object.keys(response).length;
		    if (len > 0) {
			
			for (var key in response) {
			    if (response.hasOwnProperty(key)) {
				// Print each key-value pair to the console
				errorString = errorString + key + '\n';
				console.log(key + ': ' + response[key]);
			    }
}
			//errorString = errorString + JSON.stringify(response, null, 2);
			//console.log(errorString);
		    }
		})
		.catch(errorMsg => { console.log(errorMsg); });
	    
	    iCount = iCount + iChunks;
	    width = (iCount / numberOfElements) *100;

	    if (width >= 100) {
		width = 100;
		elem.style.width = width + "%";
		elem.innerHTML = width  + "%";
		i = 0;
		var errorDiv = document.getElementById('errorDiv');

		errorDiv.style.display = 'block';
		errorDiv.innerHTML = '<pre>' + errorString + '</pre>';

		//console.log(endIndex)
		//console.log(errorString);

	    } else {
		elem.style.width = width + "%";
		elem.innerHTML = Math.floor(width) + "%";
	    }
	    // Recursive call for the next batch if there are more elements
	    if (endIndex < lines.length) {
                setTimeout(function () {
		    startIndex = endIndex;
		    endIndex = endIndex + iChunks;
                    frame();
                }, 1); // Optional delay in milliseconds
            } else {
		startIndex = 0;
		endIndex = Math.min(startIndex + iChunks, lines.length);
		i = 0;
		iCount = 0;
		width = 0;

		
		var sdfileElement = document.getElementById('sdfile');
		sdfileElement.href = "https://esox3.scilifelab.se/vialdb/dist/export/" + sToken + "/export.sdf";
		sdfileElement.textContent = 'SDFile';

	    }
	}
	frame(0);
    }
}
