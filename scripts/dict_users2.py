#!/usr/bin/env python

import pwd, grp, yaml, spwd
import sys, getopt, os


if os.geteuid() is not 0:
  print("I really need to run as root to get the crypted passwords, just sudo me")
  exit(2)

real_user = os.environ['SUDO_USER']
real_uid = int(os.environ['SUDO_UID'])

gid = ""
userlist=[]
grouplist= []
u_yaml = { }
g_yaml = { }
g_search = False
switch = False
g_only = False
keys = False
# create TLD od dictionary
# a set of sets
dict = {"grps" : {} , "users" : {} }

# create tmp dir for myself

directory = os.getenv("HOME") + "/.ansible/tmp/"
if not os.path.exists(directory):
    os.makedirs(directory)
    os.chown(directory,real_uid,-1)



h_msg='''
  what_ever_im_called.py [ -G group | -g group | -u user[,user2,user3,..] | --group=<group | --users=user[,user2,user3,..] , -g, -k, -r]

  -G gives just that group and no additionals, and adds it as an additional group
  -g generates all the users groups not just the ones searched on
  -r Role mode, put the keys and dictionary inside this role
  -k Package ssh keys up as well

'''

# need to add bad users and bad groups filter
# more error checking, ie help msgs on user or group not found

def main(argv):
   global userlist, g_search, switch, g_only, directory
   try:
      opts, args = getopt.getopt(argv,"hG:g:u:r:",["group=","users="])
   except getopt.GetoptError:
      print h_msg	
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
      	 print h_msg	
         sys.exit()
      elif opt in ("-g", "--group"):
         if switch:
	   print "only one option please"
 	   sys.exit(2)
         g_search = arg
	 switch=True
      elif opt in ("-u", "--users"):
         if switch:
	   print "only one option please"
           sys.exit(2)
	 for u in arg.split(','):
	   userlist.append(u)
	 switch=True
      elif opt in ("-G"):
         if switch:
	   print "only one option please"
 	   sys.exit(2)
         g_search = arg
         g_only = True          
	 switch=True
      elif opt in ("-r"):
        if not os.path.exists("/usr/local/ansible/roles/" + arg ):
          print "Role: " + arg + " doesnt exist "
          sys.exit(2)
        directory="/usr/local/ansible/roles/" + arg
        if not os.path.exists(directory + "/vars"):
          os.makedirs(directory  + "/vars")
          print "ops"
        if not os.path.exists(directory + "/files"):
          os.makedirs(directory  + "/files")
        directory+="/files/"

if __name__ == "__main__":
   main(sys.argv[1:])

if switch is False:
  print "Help me out a bit please"
  print h_msg
  sys.exit(2)

# get all groups then find the group we want
# then add in all users in that group and add them to the list
# store the gid as well
if g_search: 
  groups = grp.getgrall()
  for group in groups:
      if group[0] == g_search:
	if group[2] < 1000:
 	   print "I'm not going to mess with system groups, bye...."
	   exit(2)
        if 'do_not_remove_ansible_hack' in group[3]: 
          group[3].remove('do_not_remove_ansible_hack')
        userlist += group[3]
        gid = group[2]

# now find all users who have that group set as their primary group
# and add them to the list if they are not already there
  for user in pwd.getpwall():
      if user[3] == gid:
        if user[0] not in userlist:
          userlist.append(user[0])


# now we need a list of primary groups for creation
# so loop through the users grabbing the gids
# revsolve the gid into a group name and add to list of not there
#print userlist

if not g_only:
  for user in userlist:
   try:
     u = pwd.getpwnam(user)
   except KeyError:
     print "Whops looks like this user doesn't exist: %s \n" % user 
     sys.exit(2)
   g = grp.getgrgid(u[3])
 #  if g[0] not in grouplist:
  #   grouplist.append(g[0])

# start to build yaml object
# 1st get the user structure (again)
# start to setup the key pairs for each user
# then shove the whole user into the user dict

for user in userlist:
  # test the user is valid
  gg = ""
  try:
    u = pwd.getpwnam(user)
  except KeyError:
    print "Whops looks like this user doesn't exist: %s \n" % user 
    sys.exit(2)

  # build a the set for the user
  dict['users'][u[0]] = {}
  if not g_only:
    dict['grps'][user] = {}

  # populate the details
  dict['users'][u[0]]['name'] = u[0]
  # lets not monkey around with system accounts
  if u[2] < 1000:
   print "Whops looks like the account: %s is a system user as its uid is < 1000, uid: %d \n" % (user,u[2]) 
   sys.exit(2)
  dict['users'][u[0]][ 'password' ] = spwd.getspnam(user)[1] 
  if not g_only:
    dict['users'][u[0]][ 'group' ] = grp.getgrgid(u[3])[0]
  gg = user
  if g_search:
    gg = g_search
    dict['users'][u[0]][ 'groups' ] = g_search
  dict['users'][u[0]][ 'comment' ] =  u[4]
  for g in grp.getgrall():
    if user in g[3]:
      gg = gg + "," + (g[0])
      grouplist.append(g[0])
  dict['users'][u[0]][ 'groups' ] = gg
  os.system("cat " + u[5] + "/.ssh/*.pub /" + u[5] + "/.ssh/authorized_keys* | sort -u > " +  directory + "/" + user + ".keys")
#  print "cat " + u[5] + "/.ssh/*.pub /" + u[5] + "/.ssh/authorized_keys* | sort -u > " +  directory + "/" + user + ".keys"
  os.chown( directory  + user + ".keys",real_uid, -1)

# build a dict for groups
# each group as no items
for group in grouplist:
  dict['grps'][group] = {}
    
# dump the dictionary to yaml
print yaml.dump(dict,default_flow_style=False)

# if we want json uncomment the below
'''
import json
print json.dumps(dict)
'''

