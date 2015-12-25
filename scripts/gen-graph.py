#!usr/bin/python
import subprocess
import pprint
import numpy as np
from hinton import hinton
import operator

#Parsing the xml file
def get_list(cmd):
    #p = subprocess.Popen(['./get-post-owner-user-id.sh'], shell=True, executable='/bin/bash', stdout=subprocess.PIPE)
    #byte_output = p.communicate()[0]
    
    byte_output = subprocess.check_output([cmd])
    #print(byte_output)
    out_list = byte_output.decode('ascii','ignore').split('\n')
    out_list.remove('')
    return out_list

pflag = 0   # Flag to enable verbose printing
hinplot = 0 # Flag to enable hinton plots
presults = 1    # Flag to print sorted results

## Get list for postid:post_type:ownerid:parentid(onlyforans):score:AcceptedAnswerId
plist = get_list('/home/arjun/Desktop/Cornell_courses/mengproject/scripts/get-post-owner-user-id.sh')
## Remove all the owner less posts
topop = []
for i in range(len(plist)):
    if plist[i].split(':')[2] == '':
        topop.append(i)

for i in range(len(topop)):
    plist.pop(topop[i])

if pflag == 1:
    print(plist)

## Get list for Userid:displayname:Reputation
ulist = get_list('/home/arjun/Desktop/Cornell_courses/mengproject/scripts/get-user-id-name.sh')
if pflag == 1:
    print(ulist)
udict = {v.split(':')[0]:v.split(':')[1] for v in ulist}
Unq = {v.split(':')[0]:0 for v in ulist}
Una = {v.split(':')[0]:0 for v in ulist}

## Creating dict for storing cumulative votes(value) for each question(key)
qcvotesdict = {}
avotesdict = {}
uqualdict = {}

f_acc = {}
Na = {}
vq = {}

# initialisation of user quality dictionary
uqualdict = {v.split(':')[1]:[] for v in ulist}

## Printing the graph file G2
if pflag == 1:
    print("digraph G {")
## Printing all user nodes with attributes
for key in udict:
    if pflag == 1:
        print(key + " " + "[label=\"" + udict[key] + "\",shape=box,color=red]")

## Printing all post nodes with attributes + edges
## temp def: [postid,post_type(poped),ownerid,parentid,score,AcceptedAnswerId]
for post in plist:
    temp = post.split(':')
    post_type = temp.pop(1)
    if post_type == '1':
        qcvotesdict[temp[0]] = 1        # Create a key in qcvotesdict and initialise to 1(to avoid division by 0)
        f_acc[temp[4]] = 1              # flag for AcceptedAnswerId
        Na[temp[0]] = 0                 # create a key in Na
        vq[temp[0]] = int(temp[3])      # Storing votes for ques Fixme:negative vote
        if temp[1] != '':
            Unq[temp[1]] += 1               # Storing number of ques by a particular user
        if pflag == 1:
            print(temp[0] + " [shape=triangle,color=green]")    # Print ques node
            print('"' + temp[1] + '"', '->','"' + temp[0] + '"' + " [label=u2q]")   # Print user to ques edge
    elif post_type == '2':
        qcvotesdict[temp[2]] += abs(int(temp[3]))   # Add votes(score) of this answer to overall sum
        Na[temp[2]] += 1                            # Counting the number of answers for the parent ques
        if temp[1] != '':
            Una[temp[1]] += 1                           # Storing number of ans by a particular user
        if pflag == 1:
            print(temp[0] + " [shape=ellipse,color=blue,score=" + temp[3] + "]")    # Print ans node
            print('"' + temp[1] + '"', '->','"' + temp[0] + '"' + " [label=u2a,weight=" + temp[3] + "]")    # Print user to ans edge
            print('"' + temp[2] + '"', '->','"' + temp[0] + '"' + " [label=q2a,weight=" + temp[3] + "]")    # Print ques to ans edge
if pflag == 1:
    print("}")
    print(qcvotesdict)

## Calculate each answers vote ratio
## temp def: [postid,post_type(poped),ownerid,parentid,score,AcceptedAnswerId]
for post in plist:
    temp = post.split(':')
    post_type = temp.pop(1)
    if post_type == '2':
        #print("Ans")
        avotesdict[temp[0]] = int(temp[3])/qcvotesdict[temp[2]]
        if temp[1] != '':
            uqualdict[udict[temp[1]]].append(avotesdict[temp[0]])

if pflag == 1:
    print(avotesdict)
    pprint.pprint(uqualdict)

## Independent variables(knowns)
va = avotesdict
sumva = qcvotesdict
avgsumva = {}
repu = {}
for va_key in sumva:
    if Na[va_key] != 0:
        avgsumva[va_key] = sumva[va_key]/Na[va_key]
    else:
        avgsumva[va_key] = 0

## Forming system of linear equations
## temp def: [postid,post_type(poped),ownerid,parentid,score,AcceptedAnswerId]
x_theory = [p.split(':')[0] for p in plist]
for v in ulist:
    temp = v.split(':')
    x_theory.append(temp[0])
    repu[temp[0]] = int(temp[2])
N = len(plist) + len(ulist)
A = np.zeros((N,N))
B = np.zeros((N,1))
maxNa = max(list(Na.values()))
maxvq = max(list(vq.values()))
maxrepu = max(list(repu.values()))
maxavgsumva = max(list(avgsumva.values()))
idx = 0
for post in plist:
    temp = post.split(':')
    post_type = temp.pop(1)
    if post_type == '2':
        ## Implementing equation fa
        A[idx,idx] = 1
        A[idx,x_theory.index(temp[1])] = -1/3
        B[idx,0] = 1/3 * (va[temp[0]] + f_acc.get(temp[0],0))
        # Partial fu
        A[x_theory.index(temp[1]),idx] = -1/3 * 1/Una[temp[1]]  # for u_k
    elif post_type == '1':
        ## Implementing equation fq
        A[idx,idx] = 1
        if temp[1] != '':
            A[idx,x_theory.index(temp[1])] = -1/4
            A[x_theory.index(temp[1]),idx] = -1/3 * 1/Unq[temp[1]]  # for u_k, Partial fu
        B[idx,0] = 1/4 * (Na[temp[0]]/maxNa + vq[temp[0]]/maxvq + avgsumva[temp[0]]/maxavgsumva)
    idx += 1

for user in ulist:
    A[idx,idx] = 1
    B[idx,0] = 1/3 * (repu[user.split(':')[0]]/maxrepu)
    idx += 1

#print(A)
#print(B)
solution = np.linalg.solve(A,B)
out = dict(zip(x_theory,solution))
#pprint.pprint(out)

if hinplot == 1:
    hinton(A)
    hinton(B)
    hinton(solution)

## Analysing results
ans = {}
ques = {}
uuser = {}
## temp def: [postid,post_type(poped),ownerid,parentid,score,AcceptedAnswerId]
for post in plist:
    temp = post.split(':')
    post_type = temp.pop(1)
    if post_type == '2':
        ans[temp[0]] = out[temp[0]]
    elif post_type == '1':
        ques[temp[0]] = out[temp[0]]

for user in ulist:
    indx = user.split(':')[0]
    name = user.split(':')[1]
    uuser[name] = out[indx]

sorted_ans = sorted(ans.items(), key=operator.itemgetter(1))
sorted_ques = sorted(ques.items(), key=operator.itemgetter(1))
sorted_uuser = sorted(uuser.items(), key=operator.itemgetter(1))
if presults == 1:
    pprint.pprint(sorted_uuser)
    pprint.pprint(sorted_ques)
    pprint.pprint(sorted_ans)
### Printing the graph file G2
#print("digraph G {")
### Printing all user nodes with attributes
#for key in udict:
#    print(key + " " + "[label=\"" + udict[key] + "\",shape=box,color=red,quality=" + uqualdict[]"]")
#
#for post in plist:
#    temp = post.split(':')
#    post_type = temp.pop(1)
#    if post_type == '1':
#        # Print ques node
#        print(temp[0] + " [shape=triangle,color=green]")
#        # Print user to ques edge
#        print('"' + temp[1] + '"', '->','"' + temp[0] + '"' + " [label=u2q]")
#    elif post_type == '2':
#        #print("Ans")
#        # Print ans node
#        print(temp[0] + " [shape=ellipse,color=blue,score=" + temp[3] + "]")
#        # Print user to ans edge
#        print('"' + temp[1] + '"', '->','"' + temp[0] + '"' + " [label=u2a,weight=" + temp[3] + "]")
#        # Print ques to ans edge
#        print('"' + temp[2] + '"', '->','"' + temp[0] + '"' + " [label=q2a,weight=" + temp[3] + "]")
#print("}")
