%#template to generate a HTML table from a list of tuples (or list of lists, or tuple of tuples or ...)
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="{{url('assets', filepath='css/styles.css')}}">
</head>
<body style="background-color:lightblue;">
<p>The images are as follows:</p>
<div class="dropdown">
  <button class="dropbtn">Dropdown</button>
  <div class="dropdown-content">
    <a href="#">Link 1</a>
    <a href="#">Link 2</a>
    <a href="#">Link 3</a>
  </div>
</div>
<table border="1">
%for row in rows:
  <tr>
  %for col in row:
    %if ('UT' in str(col)):
      <td><a href='{{url('data', filepath=col)}}'>thumb</a></td>
    %else:
      <td>{{col}}</td>
    %end
  %end
  </tr>
%end
</table>
</body>
</html>
