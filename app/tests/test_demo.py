import contextlib
import io
import os
import tempfile
import unittest

_temp = tempfile.TemporaryDirectory()
os.environ['RENDER'] = 'true'
os.environ['DATABASE_PATH'] = os.path.join(_temp.name, 'demo.db')
with contextlib.redirect_stdout(io.StringIO()):
    from app import app, get_db, init_db

class DemoTest(unittest.TestCase):
    def test_demo_workflow(self):
        app.config.update(TESTING=True)
        c = app.test_client()
        self.assertEqual(c.get('/health').status_code, 200)
        self.assertEqual(c.get('/dashboard').status_code, 302)
        self.assertEqual(c.post('/login', data={'username':'admin','password':'wrong'}).status_code, 200)
        self.assertEqual(c.post('/login', data={'username':'admin','password':'admin123'}).status_code, 302)
        for path in ['/dashboard','/materials','/scales','/reports','/sellers','/new_transaction']:
            response = c.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertIn(b'DEMONSTRATION ONLY', response.data)
        self.assertIn(b'Main Gate Scale', c.get('/scales').data)
        self.assertTrue(c.post('/api/set_active_scale', json={'scale_id':'scale_2'}).json['success'])
        self.assertEqual(c.post('/api/set_active_scale', json={'scale_id':'invalid'}).status_code, 400)
        conn = get_db()
        material_id = conn.execute('SELECT id FROM materials LIMIT 1').fetchone()[0]
        conn.execute('UPDATE materials SET inbound_price=9.87 WHERE id=?', (material_id,))
        conn.commit()
        conn.close()
        response = c.post('/new_transaction', data={'seller_name':'Fictional Test Seller',
            'id_number':'DEMO-TEST-ONLY','material_id':material_id,'weight':'10',
            'direction':'inbound','scale_id':'scale_2'})
        self.assertEqual(response.status_code, 302)
        with contextlib.redirect_stdout(io.StringIO()):
            init_db()
        conn = get_db()
        self.assertEqual(conn.execute('SELECT inbound_price FROM materials WHERE id=?',(material_id,)).fetchone()[0], 9.87)
        self.assertEqual(conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0], 1)
        self.assertAlmostEqual(conn.execute('SELECT amount FROM transactions').fetchone()[0], 98.7)
        self.assertEqual(conn.execute('SELECT scale_id FROM scale_config WHERE is_active=1').fetchone()[0], 'scale_2')
        conn.close()
        report = c.get('/api/reports/generate?report_type=inbound&date_range=today')
        self.assertEqual(report.status_code, 200)
        self.assertTrue(report.json['success'])
        self.assertEqual(report.json['transaction_count'], 1)
        self.assertEqual(c.get('/force-add-materials').status_code, 404)
        self.assertEqual(c.get('/admin/add-scales').status_code, 404)
        c.get('/logout')
        self.assertEqual(c.post('/api/set_active_scale', json={'scale_id':'scale_1'}).status_code, 403)
        c.post('/login', data={'username':'operator','password':'operator123'})
        self.assertEqual(c.get('/dashboard').status_code, 200)
        self.assertEqual(c.post('/api/set_active_scale', json={'scale_id':'scale_1'}).status_code, 403)

if __name__ == '__main__':
    unittest.main()
