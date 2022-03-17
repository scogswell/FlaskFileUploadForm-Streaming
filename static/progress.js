// modified from  https://pythonise.com/categories/javascript/upload-progress-bar-xmlhttprequest
// Get a reference to the progress bar, wrapper & status label
var progress = document.getElementById("progress");
var progress_wrapper = document.getElementById("progress_wrapper");
var progress_status = document.getElementById("progress_status");

// Get a reference to the 3 buttons
var upload_btn = document.getElementById("upload_btn");
var loading_btn = document.getElementById("loading_btn");
var cancel_btn = document.getElementById("cancel_btn");

// Get a reference to the alert wrapper
var alert_wrapper = document.getElementById("alert_wrapper");

// Get a reference to the file input element & input label 
var input = document.getElementById("file_input");
var file_input_label = document.getElementById("file_input_label");

// Function to show alerts
function show_alert(message, alert) {

    alert_wrapper.innerHTML = `
    <div id="alert" class="alert alert-${alert} alert-dismissible fade show" role="alert">
      <span>${message}</span>
      <button type="button" class="close" data-dismiss="alert" aria-label="Close">
        <span aria-hidden="true">&times;</span>
      </button>
    </div>
  `

}

// Function to upload file
function upload(url, uuidname) {

    // Reject if the file input is empty & throw alert
    if (!input.value) {
        show_alert("No file selected", "warning")
        return;
    }

    // Create a new FormData instance
    var data = new FormData();
    // Create a XMLHTTPRequest instance
    var request = new XMLHttpRequest();
    // Set the response type
    request.responseType = "json";
    // Clear any existing alerts
    alert_wrapper.innerHTML = "";
    // Disable the input during upload
    input.disabled = true;
    // Hide the upload button
    upload_btn.classList.add("d-none");
    // Show the loading button
    loading_btn.classList.remove("d-none");
    // Show the cancel button
    cancel_btn.classList.remove("d-none");
    // Show the progress bar
    progress_wrapper.classList.remove("d-none");
    // Get a reference to the file
    var file = input.files[0];
    // Get a reference to the filename
    var filename = file.name;
    var newfilename = uuidname;
    // Get a reference to the filesize & set a cookie
    var filesize = file.size;
    document.cookie = `filesize=${filesize}`;

    // Set hidden tags to the filename from original file, and the filename we saved it in the uploads folder
    // so we can get the references in the next form on return.  These are defined in UploadForm() in forms.py
    document.getElementById('original_filename').value=filename;
    document.getElementById('saved_filename').value=newfilename;

    // Get reference to the form, we can then use new FormData()
    // to create an entire form object containing the form elements
    // to push into the next routine.  
    // https://developer.mozilla.org/en-US/docs/Web/API/Document/querySelector
    var theFormElement = document.querySelector('#theForm');
    var theFormData = new FormData(theFormElement);
    // You can't push a formData() object into another formData() object directly
    // so we just loop over all the keys and add them to our data() object
    // https://developer.mozilla.org/en-US/docs/Web/API/FormData/entries
    for (var pair of theFormData.entries()) {
        data.append(pair[0],pair[1]);
    }

    // Append the file to the FormData instance with a replacement filename (the uuid)
    data.append("file", file, newfilename);
    
    // request progress handler
    request.upload.addEventListener("progress", function (e) {

        // Get the loaded amount and total filesize (bytes)
        var loaded = e.loaded;
        var total = e.total

        // Calculate percent uploaded
        var percent_complete = (loaded / total) * 100;

        // Update the progress text and progress bar
        progress.setAttribute("style", `width: ${Math.floor(percent_complete)}%`);
        progress_status.innerText = `${Math.floor(percent_complete)}% uploaded`;
    })

    // request load handler (transfer complete)
    request.addEventListener("load", function (e) {
        if (request.status == 200) {
            show_alert(`${request.response.message}`, "success");
            // After the upload into the form data has finished, submit the form to send it back to flask.
            document.getElementById('theForm').submit();  // Can't have a button called 'submit' or this doesn't work
        }
        else {
            show_alert(`Error uploading file: ${request.response.message}`, "danger");
        }
        reset();
    });

    // request error handler
    request.addEventListener("error", function (e) {
        reset();
        show_alert(`Error uploading file`, "warning");
    });

    // request abort handler
    request.addEventListener("abort", function (e) {
        reset();
        show_alert(`Upload cancelled`, "primary");
    });

    // Open and send the request
    request.open("post", url);
    request.send(data);
    cancel_btn.addEventListener("click", function () {
        request.abort();
    })
}

// Function to update the input placeholder
function input_filename() {
    file_input_label.innerText = input.files[0].name;
}

// Function to reset the page
function reset() {

    // Clear the input
    input.value = null;
    // Hide the cancel button
    cancel_btn.classList.add("d-none");
    // Reset the input element
    input.disabled = false;
    // Show the upload button
    upload_btn.classList.remove("d-none");
    // Hide the loading button
    loading_btn.classList.add("d-none");
    // Hide the progress bar
    progress_wrapper.classList.add("d-none");
    // Reset the progress bar state
    progress.setAttribute("style", `width: 0%`);
    // Reset the input placeholder
    file_input_label.innerText = "Select file";
}
