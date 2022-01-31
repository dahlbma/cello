indexHtml="""
<!DOCTYPE html>

<!-- define angular app -->
<html ng-app="App">

<head>
  <!-- SCROLLS -->
  <meta charset="utf-8">

  <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap.min.css" />
  <link rel="stylesheet" href="//netdna.bootstrapcdn.com/font-awesome/4.2.0/css/font-awesome.css" />

  <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js"></script>
  <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/js/bootstrap.min.js"></script>

  <!-- Angular -->
  <script src="https://ajax.googleapis.com/ajax/libs/angularjs/1.3.0/angular.min.js"></script>
  <script src="https://ajax.googleapis.com/ajax/libs/angularjs/1.3.0/angular-route.js"></script>

  <!-- Angular grid gui -->
    <script src="/javascript/pdfmake.js"></script>
    <script src="/javascript/vfs_fonts.js"></script>
    <script src="/javascript/ui-grid-unstable.js"></script>
    <link rel="stylesheet" href="/javascript/ui-grid-unstable.css" type="text/css">
    <link rel="stylesheet" href="/javascript/main.css" type="text/css">
    <link rel="stylesheet" href="/static/css/local.css" type="text/css">

  <script src="javascript/app.js"></script>
</head>

<!-- define angular controller -->
<body ng-controller="mainController as mainCtrl">

  <nav class="navbar navbar-default">
    <div class="container">
      <div class="navbar-header">
        <a class="navbar-brand" href="/">DDDP Vials</a>
      </div>
      <ul class="nav navbar-nav navbar-right">
                  <div class="btn-group navbar-btn">
                    <button class="btn btn-default">Locations</button>
                    <button data-toggle="dropdown" class="btn btn-default dropdown-toggle"><span class="caret"></span></button>
                    <ul class="dropdown-menu">
                      <li><a href="#addLocation">Add new location</a></li>
                      <li><a href="#searchLocation">Search for a location</a></li>
                    </ul>
                  </div>

                  <div class="btn-group navbar-btn">
                    <button class="btn btn-default">Boxes</button>
                    <button data-toggle="dropdown" class="btn btn-default dropdown-toggle"><span class="caret"></span></button>
                    <ul class="dropdown-menu">
                      <li><a href="#addBox">Add a new box</a></li>
                      <li><a href="#searchBox">Search for a box</a></li>
                      <li><a href="#uploadBox">Upload box content</a></li>
                    </ul>
                  </div>

                  <div class="btn-group navbar-btn">
                    <button class="btn btn-default">Vials</button>
                    <button data-toggle="dropdown" class="btn btn-default dropdown-toggle"><span class="caret"></span></button>
                    <ul class="dropdown-menu">
                      <li><a href="#about">Search</a></li>
                      <li><a href="#checkinVial">Checkin</a></li>
                      <li><a href="#createEmptyVials">Create new vials from file</a></li>
                    </ul>
                  </div>

                  <div class="btn-group navbar-btn">
                    <button class="btn btn-default">Batches</button>
                    <button data-toggle="dropdown" class="btn btn-default dropdown-toggle"><span class="caret"></span></button>
                    <ul class="dropdown-menu">
                      <li><a href="#about">Search</a></li>
                    </ul>
                  </div>
      </ul>
    </div>
  </nav>


  <div id="main">
  
    <!-- angular templating -->
		<!-- this is where content will be injected -->
    <div ng-view></div>
    
  </div>
  
  <footer class="text-center">

  </footer>
  
</body>

</html>
"""

sHtml="""
<!doctype html>
<html ng-app="scotchApp">
  <head>
<meta charset="utf-8">

    <script src="http://ajax.googleapis.com/ajax/libs/angularjs/1.2.26/angular.js"></script>
    <script src="https://ajax.googleapis.com/ajax/libs/angularjs/1.2.26/angular-route.js"></script>
    <script src="http://ajax.googleapis.com/ajax/libs/angularjs/1.2.26/angular-touch.js"></script>
    <script src="http://ajax.googleapis.com/ajax/libs/angularjs/1.2.26/angular-animate.js"></script>

    <script src="http://ui-grid.info/docs/grunt-scripts/pdfmake.js"></script>
    <script src="http://ui-grid.info/docs/grunt-scripts/vfs_fonts.js"></script>
    <script src="/javascript/ui-grid-unstable.js"></script>
    <link rel="stylesheet" href="/javascript/ui-grid-unstable.css" type="text/css">
    <link rel="stylesheet" href="/javascript/main.css" type="text/css">

  </head>
  <body>

<div ng-controller="MainCtrl">
  <div id="grid1" ui-grid="{ data: myData }" ui-grid-cellNav ui-grid-pinning class="grid"></div>
</div>
    <script src="/javascript/app.js"></script>


<form id="file-form" action="uploadBox" method="POST">
  <input type="file" id="file-select" name="photos[]"/>
  <button type="submit" id="upload-button">Upload</button>
</form>


  </body>
</html>
"""

slask="""
<form enctype="multipart/form-data" action="/loadBox" method="post">
File: <input type="file" name="file1" />
<br />
<br />
<input type="submit" value="Load" />
</form>
"""
