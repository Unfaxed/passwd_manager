#!/usr/bin/env python3

import unittest
from contextlib import redirect_stdout
from io import StringIO
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from passwd import handleCmd

class CmdValsUpdateTest(unittest.TestCase):

    def setUp(self):
        self.specialChars = '!@#$%^&*()-|\\[{]}1AaZz~`_=+:;>.<,?/\"\'µåÅ'
    
    def dummyValues(self):
        return {
            'legacy_site': 'password1',
            'site1': {
                'password': 'password site_1 %s' % self.specialChars,
                'comment': None,
            },
            'site2': {
                'password': 'password site_2',
                'comment': 'comment site 2 %s' % self.specialChars,
            },
        }
    
    def test_print(self):
        vals = self.dummyValues()
        args = ['print', 'site1']
        output = StringIO()
        pw = vals['site1']['password']

        updatedVals = None
        with redirect_stdout(output):
            updatedVals, _ = handleCmd(vals, args)
        
        self.assertFalse(updatedVals)
        self.assertEqual(output.getvalue().split('\n')[0], pw)
    
    def test_list(self):
        vals = self.dummyValues()
        args = ['list']
        output = StringIO()

        correct_output = '\n'.join([
            '3 password key(s):',
            '- legacy_site',
            '- site1',
            '- site2',
            '' ])

        updatedVals = None
        with redirect_stdout(output):
            updatedVals, _ = handleCmd(vals, args)
        
        self.assertFalse(updatedVals)
        self.assertEqual(output.getvalue(), correct_output)

    def test_print_legacy(self):
        vals = self.dummyValues()
        args = ['print', 'legacy_site']
        output = StringIO()
        pw = vals['legacy_site']

        updatedVals = None
        with redirect_stdout(output):
            updatedVals, _ = handleCmd(vals, args)
        
        self.assertFalse(updatedVals)
        self.assertEqual(output.getvalue().split('\n')[0], pw)

    def test_set_not_existing(self):
        vals = self.dummyValues()
        args = ['set', 'new_site', 'new', 'Pw1$']
        
        updatedVals, _ = handleCmd(vals, args)
        
        assert updatedVals
        assert 'new_site' in vals
        assert 'password' in vals['new_site']
        assert 'comment' in vals['new_site']
        self.assertEqual(vals['new_site']['password'], 'new Pw1$')
        self.assertEqual(vals['new_site']['comment'], None)

    def test_set_existing(self):
        vals = self.dummyValues()
        args = ['set', 'Site1 ', 'new', 'site', '1', 'Pw', self.specialChars] #should still find 'site1'
        user_input = StringIO('y\n')
        fake_output = StringIO()

        updatedVals = None
        sys.stdin = user_input
        with redirect_stdout(fake_output):
            updatedVals, _ = handleCmd(vals, args)
        
        assert updatedVals
        assert 'site1' in vals
        assert 'password' in vals['site1']
        assert 'comment' in vals['site1']
        assert '[Y/n]' in fake_output.getvalue()
        self.assertEqual(vals['site1']['password'], 'new site 1 Pw %s' % self.specialChars)
        self.assertEqual(vals['site1']['comment'], None)

    def test_set_existing_legacy(self):
        vals = self.dummyValues()
        args = ['set', 'legacy_site', 'new', 'pw', self.specialChars]
        
        user_input = StringIO('y\n')
        fake_output = StringIO()

        updatedVals = None
        sys.stdin = user_input
        with redirect_stdout(fake_output):
            updatedVals, _ = handleCmd(vals, args)
        
        assert updatedVals
        assert 'legacy_site' in vals
        assert 'password' in vals['legacy_site']
        assert 'comment' in vals['legacy_site']
        assert '[Y/n]' in fake_output.getvalue()
        self.assertEqual(vals['legacy_site']['password'], 'new pw %s' % self.specialChars)
        self.assertEqual(vals['legacy_site']['comment'], None)

    def test_comment(self):
        vals = self.dummyValues()
        args = ['comment', 'site1', 'my', 'Comment', self.specialChars]

        updatedVals, _ = handleCmd(vals, args)

        assert updatedVals
        assert 'comment' in vals['site1']
        self.assertEqual(vals['site1']['comment'], 'my Comment %s' % self.specialChars)

        args2 = ['comment', 'site1', 'overriding', 'previous', 'comment', 'uwu', self.specialChars]
        updatedVals, _ = handleCmd(vals, args2)
        
        assert updatedVals
        assert 'comment' in vals['site1']
        self.assertEqual(vals['site1']['comment'], 'overriding previous comment uwu %s' % self.specialChars)
    
    def test_append_comment(self):
        vals = self.dummyValues()
        assert vals['site1']['comment'] is None
        assert vals['site2']['comment'] is not None
        site1pw = vals['site1']['password']
        site2pw = vals['site2']['password']

        args1 = ['acomment', 'site1', self.specialChars, 'New', 'Comment']

        updatedVals, _ = handleCmd(vals, args1)

        assert updatedVals
        assert 'comment' in vals['site1']
        self.assertEqual(vals['site1']['comment'], '%s New Comment' % self.specialChars)
        self.assertEqual(vals['site1']['password'], site1pw)

        args2 = ['acomment', 'site2', 'Appended', 'Comment', self.specialChars]
        updatedVals, _ = handleCmd(vals, args2)

        assert updatedVals
        assert 'comment' in vals['site2']
        self.assertEqual(vals['site2']['comment'], 'comment site 2 %s Appended Comment %s' % (self.specialChars, self.specialChars))
        self.assertEqual(vals['site2']['password'], site2pw)
    
    def test_rename(self):
        vals = self.dummyValues()
        args = ['rename', 'site2', 'another_site']
        pw = vals['site2']['password']
        comment = vals['site2']['comment']

        updatedVals, _ = handleCmd(vals, args)

        self.assertTrue(updatedVals)
        self.assertIn('another_site', vals)
        self.assertNotIn('site2', vals)
        self.assertEqual(vals['another_site']['password'], pw)
        self.assertEqual(vals['another_site']['comment'], comment)
    
    def test_delete(self):
        vals = self.dummyValues()
        args = ['delete', 'site1']

        user_input = StringIO('y\n')
        fake_output = StringIO()

        updatedVals = None
        sys.stdin = user_input
        with redirect_stdout(fake_output):
            updatedVals, _ = handleCmd(vals, args)

        self.assertTrue(updatedVals)
        self.assertIn('[Y/n]', fake_output.getvalue())
        self.assertNotIn('site1', vals)
    
    def test_generate(self):
        vals = self.dummyValues()
        args = ['gen', 'new_site']

        updatedVals, _ = handleCmd(vals, args)

        self.assertTrue(updatedVals)
        self.assertIn('new_site', vals)
        self.assertIn('password', vals['new_site'])
        self.assertGreaterEqual(len(vals['new_site']['password']), 24)
