import re
from urlparse import urlparse
import requests
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.response import Response
from pyramid.view import view_config

from assembl.lib import config
from assembl.models import File

@view_config(route_name='mime_type', request_method='HEAD')
def mime_type(request):
    url = request.params.get('url', None)
    if not url:
        raise HTTPBadRequest("Missing 'url' parameter")
    parsed = urlparse(url)
    if not parsed or parsed.scheme not in ('http', 'https'):
        raise HTTPBadRequest("Wrong scheme")
    if parsed.netloc.split(":")[0] == config.get('public_hostname'):
        # is it one of our own documents?
        r = re.match(
            r'^https?://[\w\.]+(?:\:\d+)?/data/.*/documents/(\d+)/data(?:\?.*)?$',
            url)
        if r:
            print "FOUND*****"
            document_id = r.groups(0)
            from sqlalchemy.sql.functions import func
            mimetype, create_date, size = File.default_db.query(
                File.mime_type, File.creation_date, func.length(File.data)
                ).filter_by(id=document_id).first()
            return Response(
                body=None, content_type=str(mime_type),
                content_length=size, last_modified=create_date)
    try:
        result = requests.head(url)
    except requests.ConnectionError:
        return Response(
            status=503,
            location=url)

    return Response(
        content_type=result.headers['Content-Type'],
        status=result.status_code,
        location=result.url)
