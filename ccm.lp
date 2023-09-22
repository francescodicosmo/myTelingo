
%Check, at start up, whether the input ccm is deterministic and only the final state has no out-transition. If that is not the case, stop with UNSAT.
#program initial.
state(q0).
state(qf).
state(Q) :- inc(Q,_,_).
state(Q) :- inc(_,Q,_).
state(Q) :- dec(Q,_,_,_).
state(Q) :- dec(_,Q,_,_).
state(Q) :- dec(_,_,Q,_).

countTran(Q,N,M) :- state(Q), 
                    N=#count{O,X: inc(Q,O,X)},
                    M=#count{H,K,X: dec(Q,H,K,X)}.
nonWellFormed :- countTran(Q,N,M), N+M>1.
nonWellFormed :- countTran(qf,N,M), N+M>0.

:- nonWellFormed.

%Set the initial configuration
#program initial.
conf(q0,0,0).

%At each step, perform the ccm transition
#program always.
inc(Q,O,X):-'inc(Q,O,X).
dec(Q,O,H,X):-'dec(Q,O,H,X).

conf(O,X+1,Y):-inc(Q,O,1),'conf(Q,X,Y).
conf(O,X,Y+1):-inc(Q,O,2),'conf(Q,X,Y).

conf(O,X-1,Y):-dec(Q,O,H,1),'conf(Q,X,Y),X!=0.
conf(H,0,Y):-dec(Q,O,H,1),'conf(Q,0,Y).
conf(O,X,Y-1):-dec(Q,O,H,2),'conf(Q,X,Y),Y!=0.
conf(H,X,0):-dec(Q,O,H,2),'conf(Q,X,0).

%At each step, update the list of seen configurations and check non-termination because of configuration repetition, and termination because qf has been reached. If both check fail, the ccm-checker has to continue running.
seen(X,Y,Z):-conf(X,Y,Z).
seen(X,Y,Z):-'seen(X,Y,Z).

nonTerm:-conf(X,Y,Z),'seen(X,Y,Z).
term:- conf(qf,X,Y).
running:-not nonTerm, not term.

%If, during the previous step, one of the checks passed, then stop with UNSAT. 
#program dynamic.
:-not 'running.

%Output only the current configuration, result of the checks, and the done flag.
#show conf/3.
#show running/0.
#show nonTerm/0.
#show term/0.