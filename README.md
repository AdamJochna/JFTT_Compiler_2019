# Compiler - JFTT 2019/2020
Compiler made during course <b>Formal Languages and Translation Techniques(Języki Formalne i Techniki Translacji)</b> Lecturer: <b>PhD Maciej Gębala</b>

## Technologies used
- <b>Python 3.7</b>
- <b>PLY (Python Lex-Yacc)</b>

## Compiler running and setup
To run compiler you have to use following commands under Linux:

sudo apt update
sudo apt install python3
sudo apt install python3-pip
pip3 install ply
python3 kompilator.py <input_file_name> <output_file_name>

If compilation runs without errors we are getting machine code for register machine specified in file labor4.pdf (only Polish version of pdf).
If compilation has errors we don't get file and get log of errors (for example when we want to read unassigned value).
If compilation detects warnings (possibility of reading unassigned value, but this time in if statement, this might never execute so only warning not error) we get log of warnings and get compiled .mr code.

## Virtual Machine (Register Machine)
If we want to run our .mr file on virtual machine we have directory maszyna_wirtualna wich contains virtual machine wich can run .mr files compiled by our kompilator.py. Virtual machine has to be compiled, it is written in C++ and has possibility of using large numbers library. Virtual machine was written by <b>PhD Maciej Gębala</b>

## Language specification
This is specification of language used in .imp files wich we have to compile to virtual machine code: 

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
