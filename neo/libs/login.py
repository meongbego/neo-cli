import getpass
import os
import dill
from dotenv import load_dotenv
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client
from neo.libs import utils 

home = os.path.expanduser("~")
auth_url = 'https://keystone.wjv-1.neo.id:443/v3'
user_domain_name = 'neo.id'


def get_username():
    return input("username: ")


def get_password():
    return getpass.getpass("password: ")


def generate_session(auth_url, username, password, **kwargs):
    auth = v3.Password(
        auth_url=auth_url,
        username=username,
        password=password,
        **kwargs)
    sess = session.Session(auth=auth)
    return sess


def check_env():
    return os.path.isfile("{}/.neo.env".format(home))


def create_env_file(username, password, project_id, keystone_url=None, domain_name=None):
    auth_url_temps = None
    user_domain_name_temps = None

    if not keystone_url:
        auth_url_temps = auth_url
    else:
        auth_url_temps = keystone_url

    if  not domain_name :
        user_domain_name_temps = user_domain_name
    else:
        user_domain_name_temps = domain_name

    try:
        env_file = open("{}/.neo.env".format(home), "w+")
        env_file.write("OS_USERNAME=%s\n" % username)
        env_file.write("OS_PASSWORD=%s\n" % password)
        env_file.write("OS_AUTH_URL=%s\n" % auth_url_temps)
        env_file.write("OS_PROJECT_ID=%s\n" % project_id)
        env_file.write("OS_USER_DOMAIN_NAME=%s\n" % user_domain_name_temps)
        env_file.close()
        return True
    except:
        return False


def load_env_file():
    return load_dotenv("{}/.neo.env".format(home), override=True)

def get_env_values():
    load_env_file()
    neo_env = {}
    neo_env['username'] =  os.environ.get('OS_USERNAME')
    neo_env['password'] = os.environ.get('OS_PASSWORD')
    neo_env['auth_url'] = os.environ.get('OS_AUTH_URL')
    neo_env['project_id'] = os.environ.get('OS_PROJECT_ID')
    neo_env['domain_name'] = os.environ.get('OS_USER_DOMAIN_NAME')
    return neo_env


def get_project_id(username, password, keystone_url=None, domain_name=None):
    auth_url_temps = None
    user_domain_name_temps = None

    if not keystone_url:
        auth_url_temps = auth_url
    else:
        auth_url_temps = keystone_url

    if  not domain_name :
        user_domain_name_temps = user_domain_name
    else:
        user_domain_name_temps = domain_name


    sess = generate_session(
        auth_url=auth_url_temps,
        username=username,
        password=password,
        user_domain_name=user_domain_name_temps)
    keystone = client.Client(session=sess)
    project_list = [
        t.id for t in keystone.projects.list(user=sess.get_user_id())
    ]

    return project_list[0]


def get_tenant_id(username, password, domain_name=None):
    sess = generate_session(
        auth_url=auth_url,
        username=username,
        password=password,
        user_domain_name=domain_name)
    keystone = client.Client(session=sess)
    user_id = sess.get_user_id()
    print(dir(keystone.tenant_name))
    print(keystone.users.get(user_id))


def do_login(keystone_url=None, domain_name=None):
    try:
        # don't prompt user if .neo.env exist
        if check_env():
            question = utils.question("Your Old Config Detected! Remove Env File")

            if question:
                if not domain_name:
                    domain_name = user_domain_name
                else:
                    domain_name = domain_name
                username = get_username()
                password = get_password()
                project_id = get_project_id(username, password, keystone_url=keystone_url, domain_name=domain_name)
                sess = collect_session_values(
                    username, password,
                    project_id,
                    keystone_url=keystone_url,
                    domain_name=domain_name)
                set_session(sess)

                create_env_file(username, password, project_id, keystone_url=keystone_url, domain_name=domain_name)
                utils.log_info("Login Success")
            else:
                load_env_file()
                username = os.environ.get('OS_USERNAME')
                password = os.environ.get('OS_PASSWORD')
                domain_name_env = os.environ.get('OS_USER_DOMAIN_NAME')
                auth_name_env = os.environ.get('OS_AUTH_URL')
                project_id = get_project_id(username, password, keystone_url=auth_name_env, domain_name=domain_name_env)
                set_session(collect_session_values(username, password, project_id))
                utils.log_info("Login Success")
            return True
        else:
            utils.log_warn("You don't have last login info !!")

            if not domain_name:
                domain_name = user_domain_name
            else:
                domain_name = domain_name

            username = get_username()
            password = get_password()

            project_id = get_project_id(username, password, keystone_url=keystone_url, domain_name=domain_name)

            sess = collect_session_values(
                username, password,
                project_id,
                keystone_url=keystone_url,
                domain_name=domain_name)
            set_session(sess)

            create_env_file(username, password, project_id, keystone_url=keystone_url, domain_name=domain_name)
            utils.log_info("Login Success")
            return True
    except Exception as e:
        utils.log_err(e)
        utils.log_err("Login Failed")
        return False


def do_logout():
    if check_session():
        os.remove('/tmp/session.pkl')
        remove_env = input("Remove Env File ? y=Yes, press other key to continue: ")
        if remove_env=='y':
            os.remove(home+'/.neo.env')
            utils.log_warn("Env File Removed")
        utils.log_info("Logout Success")


def collect_session_values(username, password, project_id, keystone_url=None, domain_name=None):
    auth_url_temps = None
    user_domain_name_temps = None

    if not keystone_url:
        auth_url_temps = auth_url
    else:
        auth_url_temps = keystone_url

    if  not domain_name :
        user_domain_name_temps = user_domain_name
    else:
        user_domain_name_temps = domain_name

    sess = generate_session(
        auth_url=auth_url_temps,
        username=username,
        password=password,
        user_domain_name=user_domain_name_temps,
        project_id=project_id,
        reauthenticate=True,
        include_catalog=True)
    return sess


def set_session(sess):
    try:
        with open('/tmp/session.pkl', 'wb') as f:
            dill.dump(sess, f)
    except Exception as e:
        utils.log_err("set session failed")


def get_session():
    try:
        sess = None
        with open('/tmp/session.pkl', 'rb') as f:
            sess = dill.load(f)
        return sess
    except Exception as e:
        do_login()
        return get_session()


def check_session():
    return os.path.isfile("/tmp/session.pkl")
