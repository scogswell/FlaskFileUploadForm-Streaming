# README

 A "complete" demo program flow example of using Flask to upload a file, with a form for additional information and maintaining `flask-wtf`/`wtforms` validation.  This uses `streaming-form-data` (https://github.com/siddhantgoel/streaming-form-data) to write the incoming uploaded file directly to disk instead of letting werkzeug buffer what could potentially be a very large (GB) file.  This keeps the progress bar hanging around at 100% at a potentially very long time as werkzeug  transfers the form data to the flask routine, and then the flask routine saves it.  When the bar is 100% it's done. 

This is an expansion of my other example https://github.com/scogswell/FlaskFIleUploadForm.git

This uses packages for `Flask`, `Flask-wtf`, `email-validation`, `streaming-form-data` and their dependencies.  

## How to use this

 1. Make a virtual environment:

        python -m venv .venv
        . .venv/bin/activate

 2. Install requirements automatically (flask, flask-wtf, email-validation, streaming-form-data, gunicorn):

        python -m pip install --upgrade pip 
        pip install -r requirements.txt

 3. Set development server for demo if desired:

        export FLASK_ENV=development

 4. Run!  

        flask run  

 5. Navigate in web browser to displayed url http://127.0.0.1:5000/

## Extra credit: NGINX setup 

6. Project includes config files for gunicorn and nginx to run behind a proxy.  Be like me and try to run a development test with a Linux VM running off a USB2 flash stick.You can upload a 3GB file. nginx by default will buffer the entire file (saving it in a temp space somwhere), then Werkzeug will read and buffer the file (maybe even in another temp space somwhere) and finally feed it to your flask route where you can save it to disk.  With USB2 running ~ 11 MB/sec from a VM you will find all the bottlenecks. 
   
   The nginx config turns off proxy request buffering, and by using streaming-form-data we can avoid the Werkzeug buffer so we can go directly from upload through the nginx proxy to saving on disk. 

   On your test rig, not connected directly to the internet, on Ubuntu Server 20.04 LTS you can drop one of `progress-ssl.nginx` or `progress-nossl.nginx` into `/etc/nginx/sites-enabled/` (remove "default").  If you use the ssl version you need to make certificates and set their location in the progress-ssl.nginx file.  

   As a regular user on Ubuntu, you can setup `venv` on the sane VM you have nginx on (like above).  Run `gunicorn`.  gunicorn will read configuration from gunicorn.conf.py. You should be able to load e.g. http://192.168.145.142 or whatever your VM's ip address is and nginx proxy to the flask program.  Whee technology.  

   You can comment out the line `proxy_request_buffering off;` in either nginx config to see 
   the effect of nginx buffering the entire large-file request before sending it to the flask application.

   Remember, This program doesn't do anything, it just provides the example for "a way that works" so don't leave it on the internet and get yourself pwned. 

 There are copious `print()` statments so you can follow program flow either in the terminal or in
 visual studio code. 

 This uses (some) of bootstrap4 for display (css but not js), particularly to get the progress bar graphic itself.  Bootstrap is not required otherwise. Templates are littered with bootstrap 'stuff' as a result, you could make it cleaner using either:

 `flask-bootstrap` (bootstrap 3) https://pythonhosted.org/Flask-Bootstrap/ 

 or

 `bootstrap-flask` (bootstrap4/bootstrap5) https://bootstrap-flask.readthedocs.io/en/stable/

But I have not in order to keep the code "simpler" and readable without being mired in abstraction for bootstrap.

Likewise, since this is just a demo for how to do a thing, it doesn't actually do anything with that thing, so there's no use of databasing to manage data. 

Clean out the "uploads" folder after you're done playing with it, since nothing deletes your fake uploads.

This is based on upload/progress display from https://pythonise.com/categories/javascript/upload-progress-bar-xmlhttprequest, thanks very much for this example.  

Steven Cogswell 
