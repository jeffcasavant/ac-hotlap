#! /usr/bin/env python3

import json
import os

from flask import Flask, request
import sqlite3

HOST = '0.0.0.0'
PORT = 1024
DB = 'records.sqlite'

app = Flask(__name__)

conn = sqlite3.connect(DB)
db = conn.cursor()
db.execute('CREATE TABLE IF NOT EXISTS records (driver text, track text, car text, lap real)')
conn.commit()
conn.close()

@app.route('/records', methods=['GET', 'POST'])
def records():
    if request.method == 'POST':
        data = request.get_json(force=True)
        conn = sqlite3.connect(DB)
        db = conn.cursor()
        db.execute('INSERT INTO records VALUES (?, ?, ?, ?)',
                   (data['driver'], data['track'], data['car'], data['lap']))
        conn.commit()
        conn.close()
        return 'accepted', 204
    else:
        track = request.args.get('track', default=None)
        car = request.args.get('car', default=None)
        limit = int(request.args.get('limit', default=10))

        if limit > 100:
            limit = 100

        where_clause = ''
        subs = (limit,)
        if track and car:
            where_clause = 'WHERE track = ? AND car = ?'
            subs = (track, car, limit)
        elif track:
            where_clause = 'WHERE track = ?'
            subs = (track, limit)
        elif car:
            where_clause = 'WHERE car = ?'
            subs = (car, limit)

        conn = sqlite3.connect(DB)
        db = conn.cursor()
        data = db.execute('SELECT * FROM records {} ORDER BY lap ASC LIMIT ?'.format(where_clause), subs)

        result = json.dumps([{'driver': item[0], 'track': item[1], 'car': item[2], 'lap': item[3]}
                for item in data])

        conn.close()
        return result, 200

if __name__ == '__main__':
    app.run(host=HOST, port=PORT)
