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
    <div class="select-date">
      <label for="date-select">Choose a date:</label>
      <select name="dates" id="date-select">
          % for dir in dirlist:
            <option value='{{dir}}'>{{dir}}</option>
          % end
      </select>
    </div>
    <table id="images" border="1">
      <tr>
        <th>Name</th>
        <th>Date</th>
        <th>Width</th>
        <th>Exptime</th>
        <th>Filter</th>
        <th>Frame Type</th>
        <th>Thumb</th>
      </tr>
      %for row in imlist:
        <tr>
        %for col in row:
          %if ('UT' in str(col)):
            <td><a href='{{url('data', filepath=col)}}'
                  target='popup'
                  onclick="window.open('{{url('data', filepath=col)}}',
                    'popup','width=300,height=300'); return false;"
                    >thumb</a></td>
          %else:
            <td>{{col}}</td>
          %end
        %end
        </tr>
      %end
      </table>

  <div>
  <script>
    document.getElementById("date-select").onchange = function(){
      var value = document.getElementById("date-select").value;
      if (window.location.port) {
        new_url = "http://" + window.location.hostname +
                  ":" + window.location.port + "/astrobrowse/" + value;
      } else {
        new_url = "http://" + window.location.hostname +
                  "/astrobrowse/" + value;
      }
      window.location.assign(new_url);
    };
  </script>
</body>
</html>

