%%%Provide ccm instructions as input.
%%% the initial configuration is q0.
%%% The final configuration is qf.
%%% The counters names are 1 and 2.
%%% Increment instructions are specified with the syntax
%%%     inc(<state1>,<state2>,<counter>)
%%% whch means: transition from <state1> to <state2> and increase counter <counter>
%%% Decrement instructions are specified with the syntax
%%%     dec(<state1>,<state2>,<state3>,<counter>)
%%% whch means: if counter <counter> is not empty, then decrease it and transition to <state2>; otherwise, transition to <state3>.

%inc(q0,qf,1).
inc(q0,q1,1).
inc(q1,q2,2).
dec(q2,q2,q3,1).
dec(q3,q1,qf,2).