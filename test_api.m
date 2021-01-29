import matlab.net.*
import matlab.net.http.*
r = RequestMessage;
uri = URI('http://localhost:5000/kde/');
resp = send(r,uri);
kde = resp.Body.Data.kde;

imagesc(kde)
set(gca, 'YDir', 'normal')