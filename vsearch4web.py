from cgitb import html
from flask import Flask, render_template, request, escape, session, copy_current_request_context
from DBcm import UseDataBase, ConnectionError, CredentialsError, SQLError
from checker import check_logged_in
from threading import Thread

app = Flask(__name__)

app.config['dbconfig'] = {'host': '127.0.0.1',
                'user': 'vsearch',
                'password': 'pass',
                'database':'vsearchlogDB'}

def search_letters(phrase: str, letters: str = 'aeiou') -> set:
    return set(letters).intersection(set(phrase))


@app.route('/search4', methods = ['POST'])
def do_search() -> 'html':
    @copy_current_request_context
    def log_request(req:'flask_request', res: str) -> None:
        try:
            with UseDataBase(app.config['dbconfig']) as cursor:
                _SQL = """insert into log(phrase, letters, ip, browser_string, results)
                        values(%s,%s,%s,%s,%s)"""
                cursor.execute(_SQL, (req.form['phrase'],
                                        req.form['letters'],
                                        req.remote_addr,
                                        req.headers.get('User-Agent'),
                                        res,))
        except ConnectionError as err:
            print('Is your database switched on? Error:', str(err))
        except CredentialsError as err:
            print('User-id/Password issues. Error:', str(err))
        except SQLError as err:
            print('Is your query correct? Error: ', str(err))
        except Exception as err:
            print('Something went wrong:', str(err))
        return 'Error'

    title = 'Here your results: '
    phrase = request.form['phrase']
    letters = request.form['letters']
    results =  str(search_letters(phrase, letters))
    try:
        t = Thread(target=log_request, args=(request,results))
        t.start()
    except Exception as err:
        print('Error occured: ', str(err))

    return render_template('results.html', the_title = title,
                            the_results = results, the_phrase = phrase,
                            the_letters = letters)

@app.route('/')
@app.route('/entry')
def entry_page() -> 'html':
    return render_template('entry.html',
                            the_title = 'Welcome to search_letters for web!')

@app.route('/viewlog')
@check_logged_in
def view_the_log() -> 'html':
    _SQL = """select phrase, letters, ip, browser_string, results
              from log"""

    with UseDataBase(app.config['dbconfig']) as cursor:
        cursor.execute(_SQL)
        contents = cursor.fetchall()

    titles = ('Phrase', 'Letters', 'Remote Addr', 'User Agent', 'Results')
    return render_template('viewlog.html',
                            the_title = 'View Log',
                            the_row_titles = titles,
                            the_data = contents,)

@app.route('/login')
def do_login() -> str:
    session['logged_in'] = True
    return 'You are now logged in'

@app.route('/logout')
def do_logout() -> str:
    session.pop('logged_in')
    return 'You are now logged out'


if __name__ == '__main__':
    app.run(debug=True)
