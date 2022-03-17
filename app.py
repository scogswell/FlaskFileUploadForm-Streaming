# A "complete" demo program flow example of using Flask to upload a file, with a form for 
# additional information and maintaining flask-wtf/wtforms validation.  This uses 
# streaming-form-data to write the incoming uploaded file directly to disk instead of
# letting werkzeug buffer what could potentially be a very large (GB) file.  This keeps
# the progress bar hanging around at 100% at a potentially very long time as werkzeug 
# transfers the form data to the flask routine, and then the flask routine saves it.  When
# the bar is 100% it's done. 
#
# 1. Make a virtual environment:
#       python -m venv .venv
#       . .venv.bin/activate
# 2. Install requirements automatically (flask, flask-wtf, email-validator, streaming-form-data):
#       python -m pip install --upgrade pip 
#       pip install -r requirements.txt
# 3. Set development server for demo if desired:
#       export FLASK_ENV=development
# 4. Run!  
#       flask run  
#       (alternately) python app.py
# 5. Navigate in web browser to displayed url http://127.0.0.1:5000/
#
# Extra credit: NGINX setup 
# 
# 6. Project includes config files for gunicorn and nginx to run behind a proxy.  Be like me 
#    and try to run a development test with a Linux VM running off a USB2 flash stick.
#    You can upload a 3GB file. nginx by default will buffer the entire file
#    (saving it in a temp space somwhere), then Werkzeug will read and buffer the file (maybe 
#    even in another temp space somwhere) and finally feed it to your flask route where you can
#    save it to disk.  With USB2 running ~ 11 MB/sec from a VM you will find all the bottlenecks. 
#    
#    The nginx config turns off proxy request buffering, and by using streaming-form-data we 
#    can avoid the Werkzeug buffer so we can go directly from upload through the nginx proxy
#    to saving on disk. 
#
#    On your test rig, not connected directly to the internet, on Ubuntu Server 20.04 LTS you 
#    can drop one of progress-ssl.nginx or progress-nossl.nginx into /etc/nginx/sits-enabled/ 
#    (remove "default").  If you use the ssl version you need to make certificates and set
#    their location in the progress-ssl.nginx file.  
#
#    Setup venv on the sane VM you have nginx on (like above).  Run gunicorn.  
#    gunicorn will read configuration from gunicorn.conf.py. 
#    You should be able to load e.g. http://192.168.145.142 or whatever your VM's ip address is 
#    and nginx proxy to the flask program.  Whee technology.  
#
#    You can comment out the line "proxy_request_buffering off;" in either nginx config to see 
#    the effect of nginx bufferingthe entire large-file request before sending it to the flask 
#    application.
# 
#    Remember, This program doesn't do anything, it just provides the example for "a way that works 
#    so don't leave it on the internet and get yourself pwned. 
#
# There are copious print() statments so you can follow program flow either in the terminal or in
# visual studio code. 
#
# This uses (some) of bootstrap4 for display, particularly to get the progress bar graphic itself.  
# Bootstrap is not required otherwise.  
# Templates are littered with bootstrap 'stuff' as a result, you could make it cleaner using either
# flask-bootstrap (bootstrap 3) https://pythonhosted.org/Flask-Bootstrap/ 
# or bootstrap-flask (bootstrap4/bootstrap5) https://bootstrap-flask.readthedocs.io/en/stable/
#
# Steven Cogswell 
#
# This is based on upload/progress display from https://pythonise.com/categories/javascript/upload-progress-bar-xmlhttprequest
# and expanded upon my previous example https://github.com/scogswell/FlaskFIleUploadForm.git  
#
import os, uuid, time
from flask import Flask, render_template, request, make_response, jsonify, redirect, url_for, flash, send_from_directory
from forms import UploadForm
from werkzeug.utils import secure_filename
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import ValueTarget, FileTarget

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
print("Remember FLASK_ENV=development for debugging")

app.config.update(
    UPLOADED_PATH=os.path.join(basedir, 'uploads'),  # storage for uploaded files  
    SECRET_KEY = "you-know-this"  # a SECRET_key is required for csrf forms in wtforms
)

# this is the entry point but this is just a demo program so get right to it. 
@app.route('/')
def index():
    return redirect(url_for('upload_file'))


@app.route("/upload-file", methods=["GET", "POST"])
def upload_file():
    """This routine does all the work.  The lifecycle is: 
        1. First pass: upload_file() is a blank form (name/email fields and continue button) are shown.  
           File upload widget is not shown.
        2. If, on submission, the form does not validate the name/email fields, go back to step 1
        3. If form validates, lock the name/email fields and show the upload file section
        4. The actual upload is done via XMLHttpRequest in progress.js.  The page elements are manipulated by 
           progress.js to display a progress bar and provide cancel buttons and success/error displays.  
           As part of the file upload, progress.js also pushes the form data for name/email/csrf_token along as part 
           of the request, so that in the next step we have "normal" form elements and validation available to us.  
           Also it passes along the original filename, and the file it was stored in the uploads directory. In this 
           program we save the file with a uuid for a filename so no clashes if the same file gets uploaded twice.
           When progress.js has finished POST'ing the file and additional form data, upload_file() is called again via
           javascript with a file available in the form data, upload_file() sees this and then saves the file to the local
           uploads directory set in the app.config.
           During the XMLHttpRequest upload_file() has to communicate with the javascript via JSON so it can't 
           return a template when finished.  
        5. To process the uploaded file and form data and get another template to render after the upload finishes, as a final step, 
           the upload in progress.js fires the "submit" event on the  form (which previously validated) and sends 
           everything to "completed_upload()".  We now have available to usall the data from the previous form (name/email),
           the filename of the original uploaded file, and the filename  of the file when it was saved in the uploads folder.
           You can then use database stuff (e.g. flask-sqlalchemy) to store these records.  
    """
    form = UploadForm()
    # Generate a unique uuid, we will save the file with this as the filename into the uploads folder
    # to prevent clashing
    uuidname = uuid.uuid4()  
    print("the chosen uuid name is [{}]".format(uuidname))
    print("/upload-files: here we are")
    print("/upload-files: name: [{}]".format(form.name.data))
    print("/upload-files: email: [{}]".format(form.email.data))
    # States we could get here in:
    #    A. form UploadForm not validated, either first display or a field validation failure from being submitted.  
    #    B. form UploafForm validated, no 'file' in POST data, we haven't uploaded anything yet, show the upload file controls
    #
    # If the form has validated, then we've already been through this at least once, set the flag "okaytogo=True"
    # to tell the template upload_file.html to show the upload file field and button. 
    print("/upload-files: Validating form")
    if form.validate_on_submit():
        # This is state (B) or (C) above 
        print("/upload-files: Form validated")
        print("/upload-files: name: [{}]".format(form.name.data))
        print("/upload-files: email: [{}]".format(form.email.data))
        # If no 'file' is available then we're just on the pass showing the upload button, it hasn't 
        # actually uploaded a file yet.  
        if 'file' not in request.files:
            # This is state (B) above 
            return render_template("upload_file.html", form=form, uuidname=uuidname, okaytogo=True)
        else:
            # At this point all the javascript from progress.js ran and submitted the file upload, along
            # with replicated form data for name/email/csrf_token so we have those available and the 
            # form validated.  If that form submits successfully it doesn't return to here it goes to 
            # /complete instead.   So if get to this point something weird happened. 
            print("/upload-files: Some sort of error happened")

    return render_template("upload_file.html", form=form, uuidname=uuidname)
  

@app.route("/complete", methods=["GET", "POST"])
def completed_upload():
    """
    This function gets called after the upload_file() form has validated, and the file uploaded via POST.
    """
    form=UploadForm()
    # again, don't trust filenames that might be shady.  Use secure_filename from werkzeug.  
    secure_original_name = secure_filename(form.original_filename.data)
    secure_saved_name = secure_filename(form.saved_filename.data)
    print("/complete: name is [{}] email is [{}]".format(form.name.data, form.email.data))
    print("/complete: original file name is [{}]".format(secure_original_name))
    print("/complete: saved filename is [{}]".format(secure_saved_name))
    # This should validate, since everything was validated before we came in.  
    if form.validate_on_submit():
        print("/complete: we have validated")
        # You could do more things like do database work storing information since you have all the 
        # information now in the UploadForm() data.
        return render_template('completed.html', form=form)
    else:
        # Everything validated before so we shouldn't get here unless something went terribly terribly wrong.  
        print("/complete: errors {}".format(form.errors))
        for error in form.name.errors:
            flash("Name: {}".format(error))
        for error in form.email.errors:
            flash("Email: {}".format(error))    
        return redirect(url_for('upload_file'))

@app.route("/api/upload", methods=["GET", "POST"])
def stream_upload():
    """
    For large file uploads (e.g. 3 GB in my tests), Werkzeug will buffer the entire POST request 
    including the mutipart with the file in it and then transfers it when you use an instruction like
    form=UploadForm or request.files.  This will make the progress upload spin and wait a long time
    at 100% upload until Werkzeug transfers the POST data and then FileStorage.save saves it to 
    disk.  This also means there's likely two copies of the large file in temp storage somewhere 
    while all this is going on.  

    Instead, we use a technique shown in 'streaming-form-data' where we read the POST data in 
    chunks as it's coming in, and save the file as we go, rather than waiting for the whole thing to buffer
    up.  This can be much, much faster especially on systems with slow storage.  

    The downside is that don't have all the form elements available before we start writing the file,
    so we end up writing it to a temporary file.  Once we've streamed the entire POST we can rename
    it to the correct filename using the extra formData passed in from the progress.js functions.

    We wrap all filenames with secure_filename from Werkzeug, even though the names *should* be safe
    but who knows what shady stuff can happen. 

    This is a JSON function that communicates only with the XMLHttpRequest function in progress.js, 
    so it can't return templates or other flask-style actions.  We count on upload() in progress.js
    to actually fire the event when transfer is completed to submit the final form element and 
    take us to /complete.
    
    https://github.com/siddhantgoel/streaming-form-data
    https://streaming-form-data.readthedocs.io/en/latest/
    https://sgoel.dev/posts/streaming-multipart-form-data-parser-for-python/
    """
    print("/stream_upload: in stream_upload")
    if request.method == "POST":
        parser = StreamingFormDataParser(headers=request.headers)

        # We use a uuid4 name to hopefully not clash with any existing files, and use "temp-" in front to really
        # hammer it home.  We purposely save the temp-uuid4 file in the uploads directory so when we
        # do a rename it doesn't mean yet another multi-gigabyte file copy.  
        temp_uuidname=os.path.join(app.config['UPLOADED_PATH'],secure_filename("temp-"+str(uuid.uuid4())))
        name_target=ValueTarget()
        email_target=ValueTarget()
        file_target = FileTarget(temp_uuidname)

        parser.register('name', name_target)   # extra formData we passed in
        parser.register('email', email_target) # extra formData we passed in 
        parser.register('file', file_target)   # the file being uploaded 

        # loop and read chunks and pass them to the parser until we run out of chunks
        print("/stream_upload: reading chunks")
        chunks=0
        start_time = time.perf_counter()    # for benchmarking
        while True:
            chunk = request.stream.read(16384)
            if not chunk:
                break
            parser.data_received(chunk)
            chunks += 1
        end_time = time.perf_counter()      # for benchmarking 
        print("/stream_upload: {} chunks read".format(chunks))
        print("/stream_upload: {} seconds upload time".format(end_time-start_time))

        new_filename = os.path.join(app.config['UPLOADED_PATH'], secure_filename(file_target.multipart_filename))
        print("/stream_upload: temp file is {}".format(temp_uuidname))
        print("/stream_upload: final file is {}".format(new_filename))

        # This JSON function doesn't know ahead of time what the destination filename 
        # for the file is.  It gets set up in the form data but because we start immediately
        # streaming the file to storage we don't know the name first.  But that's okay,
        # we saved it as a temp filename with a uuid so no clashing hopefully, then
        # just rename it when done, when we know the true filename
        #
        # Note we saved it in the destination directory so hopefully os.rename() 
        # doesn't take long to do it.  
        #
        # We test to make sure we're not clobbering an existing file... just in case.  
        if (os.path.isfile(new_filename) is False):
            try:
                os.rename(temp_uuidname,new_filename)
            except OSError:
                res = make_response(jsonify({"message": "Error renaming file"}), 400)
                return res
        else:
            res = make_response(jsonify({"message": "File already exists"}), 400)
            return res

        print("/stream_upload: renamed file successfully")
        print("/stream_upload: name from POST was {}".format(name_target.value.decode('utf8')))
        print("/stream_upload: email from POST was {}".format(email_target.value.decode('utf8')))
        print("/stream_upload: file from POST was {} ({})".format(file_target.multipart_filename, file_target.multipart_content_type))

        # We responsd via JSON back to the progress.js upload function to let it know we're done
        # and it can stop the spinner and do the final form submission.  
        res = make_response(jsonify({"message": "File uploaded"}), 200)
        return res
    else:
        res = make_response(jsonify({"message": "no post data"}), 400)
        return res


@app.route("/download", methods=[ "GET", "POST"])
def download_file():
    """
    Provide a download link to get the file back, just to demonstrate using the attachment_filename
    paramater so you can return the file with it's original name from the uuid storage name. 
    As usual use werkzeug's secure_filename to make sure the filename isn't doing some shady stuff.
    """
    uuid = request.args.get('uuid')
    filename = secure_filename(request.args.get('filename'))
    storagedirectory = app.config['UPLOADED_PATH']
    print("Download {} as {}".format(uuid, filename))
    return send_from_directory(directory=storagedirectory, path=uuid, as_attachment=True, attachment_filename=filename)


if __name__ == '__main__':
    app.run(debug=True)