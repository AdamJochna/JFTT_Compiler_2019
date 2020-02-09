# Compiler - JFTT 2019/2020
Compiler made during course <b>Formal Languages and Translation Techniques(Języki Formalne i Techniki Translacji)</b> Lecturer: <b>PhD Maciej Gębala</b>

## Compiler score:
Compiler scored 4th out of total 112 compilers send to our lecturer for scoring. We were being scored by effectiveness of our final machine code.Each instruction was assigned cost (specified in labor4.pdf). Each test run by our lecturer was scored by ranks of sum of all instructions costs. Final score of compiler was sum of places at each test. For example my compiler was ranked 4th with score 69 = 10 + 11 + 1 + 1 + 3 + 4 + 39 . My compiler was best on two tests. It is worth noting that we never knew what tests we will be graded on and this is still a secret.

![My compiler is the 4th with SumaM=69](https://github.com/AdamJochna/JFTT_Compiler_2019/blob/master/imgs/leaderboard.jpg)


## Optimizations used in compiler:
I focused mainly on optimizing machine code, not so much on opitimizing AST tree. Code you see here is final version of compiler, but my developer version cosists of testing environment which was crucial. If our code gives wrong answer we get 200 penalty so with one error out of my score would be 268 and I would land on ~30th place. So optimization is worth doing only when it works (xD). My procedure for optimization was tests driven and at the beggining I focused on writing heavy tests with many corner cases and randomized tests generated with python code and python generated answers then translated to .imp code to assure answers are true. Then I tried to optimize sum of costs of all tests. A the end I ended up having 10 times lower operations cost.

Here I list optimizations used (some of them I have forgotten):
- I found way to make squaring numbers faster this is useful during prime fastor decomposition or other algorithms, I used fact that I can cheaply make lookup table for squares i^2 for i in range 0-2^6 this allowed me to avoid making 6 primary loops in binary decomposing i for numbers in range 0-2^12 this is 50% boost which is a lot, worth noticing is that I used this algorithm only when program contained VARIABLE TIMES VARIABLE otherwise lookup table was not generated.Also decomposing smaller number of two is cheaper than naivly decomposing first number in statement example x*y = bin(x)*y (naive) = bin(min(x,y))*max(x,y) (better)

![Equation that was the building block to efficient number squaring](https://github.com/AdamJochna/JFTT_Compiler_2019/blob/master/imgs/eq.jpg)

- I used binary decomposition in calculating modulo and div but instead decomposing binary i decomposed numbers in quadrary system, this allowed me to avoid making calculations seeing if value is smaller than zero then backtracking. Adding smaller numbers but more often is better in this case. Also I made switch cases when complier was making mod or div with 2 this could be done cheaply with shift operations.
- I used binary logic where values x>0 have binary value true and x<= have binary value false this allowed me to avoid generating 0 and 1 which is not efficient, instead in cases when comparing x>y or x>=y i could subtract numbers change signs(depending on inequality) and subtract or add 1 which is cheap.
- I used costant increments for example X PLUS 1 is just incrementing X by 1, naive way is to make variable assign 1 then add variable to X and assign it to X,
some people did this that way, which was inefficient. My program detected constants especially small like -2 -1 0 1 2.

## Technologies used
- <b>Python 3.7</b>
- <b>PLY (Python Lex-Yacc)</b>

## Compiler running and setup
To run compiler you have to use following commands under Linux:

- <b>sudo apt update</b>
- <b>sudo apt install python3</b>
- <b>sudo apt install python3-pip</b>
- <b>pip3 install ply</b>
- <b>python3 kompilator.py <input_file_name> <output_file_name></b>

If compilation runs without errors we are getting machine code for register machine specified in file labor4.pdf (only Polish version of pdf).
If compilation has errors we don't get file and get log of errors (for example when we want to read unassigned value).
If compilation detects warnings (possibility of reading unassigned value, but this time in if statement, this might never execute so only warning not error) we get log of warnings and get compiled .mr code.

## Virtual Machine (Register Machine)
If we want to run our .mr file on virtual machine we have directory maszyna_wirtualna which contains virtual machine which can run .mr files compiled by our kompilator.py. Virtual machine has to be compiled, it is written in C++ and has possibility of using large numbers library. Virtual machine was written by <b>PhD Maciej Gębala</b>

## Language specification
This is specification of language used in .imp files which we have to compile to virtual machine code: 

	program       -> DECLARE declarations BEGIN commands END
				  | BEGIN commands END

	declarations  -> declarations, pidentifier
				  | declarations, pidentifier(num:num)
				  | pidentifier
				  | pidentifier(num:num)

	commands      -> commands command
				  | command

	command       -> identifier ASSIGN expression;
				  | IF condition THEN commands ELSE commands ENDIF
				  | IF condition THEN commands ENDIF
				  | WHILE condition DO commands ENDWHILE
				  | DO commands WHILE condition ENDDO
				  | FOR pidentifier FROM value TO value DO commands ENDFOR
				  | FOR pidentifier FROM value DOWNTO value DO commands ENDFOR
				  | READ identifier;
				  | WRITE value;

	expression    -> value
				  | value PLUS value
				  | value MINUS value
				  | value TIMES value
				  | value DIV value
				  | value MOD value

	condition     -> value EQ value
				  | value NEQ value
				  | value LE value
				  | value GE value
				  | value LEQ value
				  | value GEQ value

	value         -> num
				  | identifier

	identifier    -> pidentifier
				  | pidentifier(pidentifier)
				  | pidentifier(num)
			  


Example code written in .imp language:

    [Prime numbers decomposition]
    DECLARE
        n; m; reminder; power; divider;
    IN
        READ n;
        divider := 2;
        m := divider * divider;
        WHILE n >= m DO
            power := 0;
            reminder := n % divider;
            WHILE reminder = 0 DO
                n := n / divider;
                power := power + 1;
                reminder := n % divider;
            ENDWHILE
            IF power > 0 THEN [ is divider found? ]
                WRITE divider;
                WRITE power;
            ELSE
                divider := divider + 1;
                m := divider * divider;
            ENDIF
        ENDWHILE
        IF n != 1 THEN [ last divider ]
            WRITE n;
            WRITE 1;
        ENDIF
    END

Specific information about language and virtual machine can be found in file `labor4.pdf`
