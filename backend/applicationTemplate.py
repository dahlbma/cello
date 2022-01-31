indexHead="""
<!DOCTYPE html>

<!-- define angular app -->
<html ng-app="App">

<head>
  <!-- SCROLLS -->
  <meta charset="utf-8">

  <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.3.2/css/bootstrap.min.css" />
  <link rel="stylesheet" href="//netdna.bootstrapcdn.com/font-awesome/4.3.0/css/font-awesome.css" />

  <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js"></script>
  <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.2/js/bootstrap.min.js"></script>

  <!-- Angular -->
  <script src="https://ajax.googleapis.com/ajax/libs/angularjs/1.3.14/angular.min.js"></script>
  <script src="https://ajax.googleapis.com/ajax/libs/angularjs/1.3.14/angular-route.js"></script>

  <!-- Angular grid gui -->
    <script src="/javascript/ui-grid/pdfmake.js"></script>
    <script src="/javascript/ui-grid/vfs_fonts.js"></script>
    <script src="/javascript/ui-grid/ui-grid.js"></script>
    <link rel="stylesheet" href="/javascript/ui-grid/ui-grid.css" type="text/css">
    <link rel="stylesheet" href="/javascript/main.css" type="text/css">
    <link rel="stylesheet" href="/static/css/local.css" type="text/css">

  <script src="javascript/app.js"></script>
</head>
"""
indexHtml="""
<!-- define angular controller -->
<body ng-controller="mainController as mainCtrl">

  <nav class="navbar navbar-default">
    <div class="container">
      <div class="navbar-header">
        <a class="navbar-brand" href="/">DDDP Vials</a>
      </div>

      <ul class="nav navbar-nav navbar-right">

         {%if user_name != None%}
           <div class="btn-group navbar-btn">
             <button class="btn btn-default">Microtubes</button>
             <button data-toggle="dropdown" class="btn btn-default dropdown-toggle"><span class="caret"></span></button>
             <ul class="dropdown-menu">
               <li><a href="#getMicrotubes">Get microtubes by batch</a></li>
               <li><a href="#getRack">Get rack</a></li>
               <li><a href="#uploadMicrotubeRack">Update rack contents</a></li>
             </ul>
           </div>

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
               <li><a href="#updateBox">Update box content</a></li>
             </ul>
           </div>

           <div class="btn-group navbar-btn">
             <button class="btn btn-default">Vials</button>
             <button data-toggle="dropdown" class="btn btn-default dropdown-toggle"><span class="caret"></span></button>
             <ul class="dropdown-menu">
               <li><a href="#editVial">Edit vial</a></li>
               <li><a href="#createEmptyVials">Add tare to vials</a></li>
               <li><a href="#createEmptyVialsNLabels">Create empty vials</a></li>
             </ul>
           </div>

           <div class="btn-group navbar-btn">
             <button class="btn btn-default">Search</button>
             <button data-toggle="dropdown" class="btn btn-default dropdown-toggle">
                <span class="caret"></span></button>
             <ul class="dropdown-menu">
               <li><a href="#searchVial">Search for vial</a></li>
               <li><a href="#searchVials">Search for vials</a></li>
               <li><a href="#searchBatches">Search for batches</a></li>
             </ul>
           </div>
         {% end %}
           &nbsp;
           &nbsp;
           <div class="btn-group navbar-btn">
              {%if user_name != None%}
                {{user_name}}
                <br>
                <a href="/logout">Logout</a>
              {% else %}
                <br>
                <a href="/login">Login</a>
              {% end %}
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
notAuthorizedHtml="""

<!-- define angular controller -->
<body ng-controller="mainController as mainCtrl">

  <nav class="navbar navbar-default">
    <div class="container">
      <div class="navbar-header">
        <a class="navbar-brand" href="/">DDDP Vials</a>
      </div>
      <ul class="nav navbar-nav navbar-right">
           <div class="btn-group navbar-btn">
                <br>
                <a href="/login">Login</a>
           </div>
      </ul>
    </div>
  </nav>
</body>
</html>
"""
