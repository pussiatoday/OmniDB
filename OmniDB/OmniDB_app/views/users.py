from django.http import HttpResponse
from django.template import loader
from django.http import JsonResponse
from django.core import serializers
from django.shortcuts import redirect
import uuid
import json

import sys
sys.path.append("OmniDB_app/include")

import Spartacus.Database, Spartacus.Utils
import OmniDatabase
from Session import Session
from OmniDB import settings


def index(request):

    #Invalid session
    if not request.session.get('omnidb_session'):
        request.session ["omnidb_alert_message"] = "Session object was destroyed, please sign in again."
        return redirect('login')

    v_session = request.session.get('omnidb_session')

    context = {
        'session' : v_session,
        'menu_item': 'users',
        'omnidb_version': settings.OMNIDB_VERSION,
    }

    template = loader.get_template('OmniDB_app/users.html')
    return HttpResponse(template.render(context, request))

def get_users(request):

    v_return = {}
    v_return['v_data'] = ''
    v_return['v_error'] = False
    v_return['v_error_id'] = -1

    #Invalid session
    if not request.session.get('omnidb_session'):
        v_return['v_error'] = True
        v_return['v_error_id'] = 1
        return JsonResponse(v_return)

    v_session = request.session.get('omnidb_session')
    v_cryptor = request.session.get('cryptor')

    try:
        v_users = v_session.v_omnidb_database.v_connection.Query('''
            select *
            from users
            order by user_id
        ''')
    except Exception as exc:
        v_return['v_data'] = str(exc)
        v_return['v_error'] = True
        return JsonResponse(v_return)

    v_user_list = []
    v_user_id_list = []

    for v_user in v_users.Rows:
        v_user_data_list = []
        v_user_data_list.append(v_user["user_name"])
        try:
            v_user_data_list.append(v_cryptor.Decrypt(v_user["password"]))
        except Exception as exc:
            v_user_data_list.append(v_user["password"])
        v_user_data_list.append(v_user["super_user"])
        v_user_data_list.append('''<img src='/static/OmniDB_app/images/tab_close.png' class='img_ht' onclick='removeUser("{0}")'/>'''.format(v_user["user_id"]))

        v_user_list.append(v_user_data_list)
        v_user_id_list.append(v_user["user_id"])

    v_return['v_data'] = {
        'v_data': v_user_list,
        'v_user_ids': v_user_id_list
    }

    return JsonResponse(v_return)

def new_user(request):

    v_return = {}
    v_return['v_data'] = ''
    v_return['v_error'] = False
    v_return['v_error_id'] = -1

    #Invalid session
    if not request.session.get('omnidb_session'):
        v_return['v_error'] = True
        v_return['v_error_id'] = 1
        return JsonResponse(v_return)

    v_session = request.session.get('omnidb_session')

    try:
        v_session.v_omnidb_database.v_connection.Execute('''
            insert into users values (
            (select coalesce(max(user_id), 0) + 1 from users),'user' || (select coalesce(max(user_id), 0) + 1 from users),'',1,'14',1,0,'{0}')
        '''.format(str(uuid.uuid4())))
    except Exception as exc:
        v_return['v_data'] = str(exc)
        v_return['v_error'] = True
        return JsonResponse(v_return)

    return JsonResponse(v_return)

def remove_user(request):

    v_return = {}
    v_return['v_data'] = ''
    v_return['v_error'] = False
    v_return['v_error_id'] = -1

    #Invalid session
    if not request.session.get('omnidb_session'):
        v_return['v_error'] = True
        v_return['v_error_id'] = 1
        return JsonResponse(v_return)

    v_session = request.session.get('omnidb_session')

    json_object = json.loads(request.POST.get('data', None))
    v_id = json_object['p_id']

    try:
        v_user_key = v_session.v_omnidb_database.v_connection.ExecuteScalar('''
            select user_key
            from users
            where user_id = {0}
        '''.format(v_id))

        v_session.v_omnidb_database.v_connection.Execute('''
            delete from users
            where user_id = {0}
        '''.format(v_id))
    except Exception as exc:
        v_return['v_data'] = str(exc)
        v_return['v_error'] = True
        return JsonResponse(v_return)

    return JsonResponse(v_return)

def save_users(request):

    v_return = {}
    v_return['v_data'] = ''
    v_return['v_error'] = False
    v_return['v_error_id'] = -1

    #Invalid session
    if not request.session.get('omnidb_session'):
        v_return['v_error'] = True
        v_return['v_error_id'] = 1
        return JsonResponse(v_return)

    v_session = request.session.get('omnidb_session')
    v_cryptor = request.session.get('cryptor')

    json_object = json.loads(request.POST.get('data', None))
    v_data = json_object['p_data']
    v_user_id_list = json_object['p_user_id_list']

    v_index = 0

    try:
        for r in v_data:
            v_session.v_omnidb_database.v_connection.Execute('''
                update users
                set user_name = '{0}',
                    password = '{1}',
                    super_user = '{2}'
                where user_id = {3}
            '''.format(r[0],v_cryptor.Encrypt(r[1]),r[2],v_user_id_list[v_index]))
            v_index = v_index + 1
    except Exception as exc:
        v_return['v_data'] = str(exc)
        v_return['v_error'] = True
        return JsonResponse(v_return)

    return JsonResponse(v_return)
