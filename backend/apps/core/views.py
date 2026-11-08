from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


@login_required
def home(request):
    return HttpResponse(
        f"<h1>LocalGRC</h1>"
        f"<p>Logged in as {request.user.email}.</p>"
        '<p><a href="/risks/">Risks</a> | '
        '<a href="/risks/matrix/">Matrix</a> | '
        '<a href="/risks/assets/">Assets</a> | '
        '<a href="/frameworks/">Frameworks</a> | '
        '<a href="/controls/">Controls</a> | '
        '<a href="/controls/coverage/">Coverage</a> | '
        '<a href="/policies/">Policies</a> | '
        '<a href="/audits/">Audits</a> | '
        '<a href="/vendors/">Vendors</a> | '
        '<a href="/incidents/">Incidents</a> | '
        '<a href="/incidents/dashboard/">Deadlines</a> | '
        '<a href="/evidence/">Evidence</a> | '
        '<a href="/evidence/dashboard/">Evidence dashboard</a> | '
        '<a href="/admin/">Admin</a></p>'
    )