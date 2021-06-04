<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="{{url('assets', filepath='css/styles.css')}}">
</head>
<body style="background-color:lightblue;">
  <div class="banner">
    <div class="banner-content">
      Lowell Astrophotography Project Database
    </div>
  </div>
  <div class="main-content">
    % for image in colorlist:
      <h2>{{image}}</h2>
      <img src="{{url('data', filepath='color/' + image)}}" width=1200>
    % end
  <div>
</body>
</html>

