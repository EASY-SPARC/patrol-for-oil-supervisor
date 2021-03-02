import matlab.net.http.*
import matlab.net.http.field.*
request = RequestMessage( 'POST', ...
    [ContentTypeField( 'application/vnd.api+json' ), AcceptField('application/vnd.api+json')], ...
    '{"xgrid": "21", "ygrid": "38", "lon": "[]", "lat": "[]"}' );
response = request.send('http://localhost:5000/robot_fb/');