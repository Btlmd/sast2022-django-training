from django.http import (
    HttpRequest,
    JsonResponse,
    HttpResponseNotAllowed,
)
from lb.models import Submission, User
from django.forms.models import model_to_dict
from django.db.models import F
import json
from lb import utils
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.views.decorators.http import require_http_methods as method

def hello(req: HttpRequest):
    return JsonResponse({
        "code": 0,
        "msg": "hello"
    })

# TODO: Add HTTP method check
def leaderboard(req: HttpRequest):
    return JsonResponse(
        utils.get_leaderboard(),
        safe=False,
    )


@method(["GET"])
def history(req: HttpRequest, username: str):
    # TODO: Complete `/history/<slug:username>` API

    raise NotImplementedError


@method(["POST"])
@csrf_exempt
def submit(req: HttpRequest):
    # TODO: Complete `/submit` API

    raise NotImplementedError


@method(["POST"])
@csrf_exempt
def vote(req: HttpRequest):
    if 'User-Agent' not in req.headers \
            or 'requests' in req.headers['User-Agent']:
        return JsonResponse({
            "code": -1
        })

    # TODO: Complete `/vote` API

    raise NotImplementedError
