from f0cal.bootstrap.helpers import GithubAPI


def auth(username, password):
    return GithubAPI(username=username, password=password).get_auth()
