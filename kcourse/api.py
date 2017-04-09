from flask import Flask, request, jsonify, make_response, url_for
from kcourse.data import DataFolder, ResultsFolder
from scripts.runner_lookup import build_runner_index


def make_app():
    data_folder = DataFolder('data')
    result_folder = ResultsFolder('results')

    result_to_race, race_to_result = data_folder.result_to_race_index
    runner_index = build_runner_index(data_folder, result_folder)

    app = Flask(__name__)

    @app.route('/api/runners/<name>')
    def hello(name):
        print name
        runner_results = runner_index[name.lower()]

        data = {
            'runner': name,
            'results': [r.to_json() for r in runner_results]
        }

        return jsonify(data)

    @app.route('/api/races/<race_id>')
    def races(race_id):
        # race_id = request.args.get('id')
        assert race_id
        rinfo_table = data_folder.raceinfo
        rinfo = rinfo_table[race_id]
        data = rinfo.to_json()
        data['id'] = race_id

        if race_id in race_to_result:
            result_id = race_to_result[race_id]
            result_url = '/api/results/' + result_id
            data['result_id'] = result_id
            data['result_url'] = result_url
        return jsonify(data)

    @app.route('/api/results/<result_id>')
    def results(result_id):
        # result_id = request.args.get('id')
        assert result_id
        csv_sio = result_folder[result_id].raw_csv()
        output = make_response(csv_sio.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=%s.csv" % result_id
        output.headers["Content-type"] = "text/csv"
        return output

    return app


if __name__ == '__main__':
    app = make_app()
    app.run()
