#!/usr/bin/env python

import os
import pygit2

url = 'https://github.com/mickep76/pepa.git'
path = '/tmp/pepa'
fn = 'test.txt'

r = pygit2.clone_repository(url, path)
r.checkout('HEAD')

c = r.revparse_single('HEAD')

f = open(path + '/' + fn, 'w')
f.write('TEST\n')
f.close()

b = r.create_blob_fromdisk(path + '/' + fn)
bld = r.TreeBuilder(c.tree)
bld.insert(fn, b, os.stat(path + '/' + fn).st_mode )
t = bld.write()
 
r.index.read()
r.index.add(fn)
r.index.write()

s = pygit2.Signature('John Doe', 'John.Doe@Foobar.com')
c = r.create_commit('HEAD', s, s, 'Added a test file', t, [c.oid])

remote = r.remotes[0]

# Requires HTTP Basic Auth. which is not supported yet
#remote.push('refs/heads/master')
