/*  DSE 201 Final - Winter 2017
	Joshua Wilson - A53228518
	jsw037@eng.ucsd.edu
	
Problem 1:
True or False (no justification required)? User-defined functions (UDFs) are
not allowed in any of your solutions.

	1. Consider a schema in which each pair of distinct tables has disjoint column 
	names. Then every SQL query Q with aliases (tuple variables) over this schema 
	can be reformulated to a query Q’ without aliases, over the same schema, such 
	that Q’ always returns the same answer as Q on every input database.

	2. SELECT * FROM T WHERE T.A <= 39 OR T.A > 39 always returns the same result as 
	SELECT * FROM T.

	3. NATURAL LEFT JOIN is SQL-expressible without the JOIN keyword.

	4. SELECT DISTINCT T.A FROM T is SQL-expressible without the DISTINCT keyword.

	5. SELECT MAX (R.A) FROM R can be expressed without the MAX built-in aggregate, 
	ORDER BY, LIMIT, TOP K, WINDOW and without UDFs.

	6. Let R(A,B) and S(B,C) be tables whose underlined attributes are primary keys. 
	Attribute R.B is not null, and it is a foreign key referencing S.  
	SELECT r.A FROM R r, S s WHERE r.B = s.B always returns the same answer as 
	SELECT A FROM R.

	7. EXCEPT can be expressed in SQL without using the EXCEPT keyword or UDFs.

	8. In SQL, all nested queries without correlated variables can be unnested 
	(without creating views or auxiliary tables).

	9. Consider tables R(A,B) and S(A,B). Then SELECT A FROM (R UNION S) always 
	returns the same result as (SELECT A FROM R) UNION (SELECT A FROM S).
	
	10. Let R(A,B) be a relation with primary key A and numeric, not-null B. Then 
	SELECT A, MAX(B) FROM R GROUP BY A returns R.
	
---- ANSWERS:
	
	1.  True
	2.  False
	3.  True
	4.  True
	5.  True
	6.  True
	7.  True
	8.  False
	9.  False
	10. True
	
/******************************************************

Problem 2:
In a soccer league each team has a home stadium, and each pair of teams faces each 
other twice during the season (once at the home stadium of each team). For a given 
match, the team whose stadium hosts the match is the home team, while the other team 
is the visitors team. We model information about the league using the schema

Teams (name, coach)
Matches (hTeam, vteam, hScore, vScore)

where name is the primary key for table Teams and coach is a candidate key for 
the same table. Attributes hTeam and vteam denote the home, respectively visitors 
team. They are foreign keys referencing the Teams table. Their value cannot be null. 
The pair hTeam, vteam is the primary key for table Matches. hScore/vScore denote the 
score of the home/visitors team, respectively. The Matches table refers only to 
completed matches, listing their final scores which are not null.

Express the following in SQL:
*/

-- various views to help with subsequent queries
CREATE VIEW home_winners AS
SELECT m.hteam as winner, m.vteam as loser
FROM matches m
WHERE m.hscore > m.vscore;

CREATE VIEW away_winners AS
SELECT m.vteam as winner, m.hteam as loser
FROM matches m
WHERE m.hscore < m.vscore;

CREATE VIEW all_winners AS
SELECT *
FROM home_winners
UNION ALL
SELECT *
FROM away_winners;

CREATE VIEW ties AS
SELECT m.hteam AS name
FROM matches m
WHERE m.hscore = m.vscore
UNION ALL
SELECT m.vteam AS name
FROM matches m
WHERE m.hscore = m.vscore;

CREATE VIEW home_win_counts AS
SELECT t.name, count(h.winner) AS home_wins
FROM teams t LEFT JOIN home_winners h ON t.name = h.winner
GROUP BY t.name
ORDER BY t.name;

CREATE VIEW away_win_counts AS
SELECT t.name, count(a.winner) AS away_wins
FROM teams t LEFT JOIN away_winners a ON t.name = a.winner
GROUP BY t.name
ORDER BY t.name;

CREATE VIEW tie_counts AS
SELECT tm.name, count(ts.name) AS ties
FROM teams tm LEFT JOIN ties ts ON tm.name = ts.name
GROUP BY tm.name
ORDER BY tm.name;

/******************************************************/

-- (i)  Count the victories of team ”San Diego Sockers”.
-- Return a single column called ”wins”.

PREPARE count_wins (text) AS
SELECT count(*) as wins
FROM all_winners
WHERE winner = $1;

--To invoke this parameterized query for team X, 
--call EXECUTE count_wins (X);
--e.g. EXECUTE count_wins ('San Diego Sockers');

/******************************************************/

-- (ii)  According to league rules, a defeat results in 0 points, a tie in 1 point, 
-- a victory at home in 2 points, and a victory away in 3 points.  For each team, return 
-- its name and total number of points earned. Output a table with two columns: 
-- name and points.

SELECT t.name, (2*h.home_wins + 3*a.away_wins + tc.ties) as points
FROM teams t LEFT JOIN home_win_counts h ON t.name = h.name
	LEFT JOIN away_win_counts a ON t.name = a.name
    LEFT JOIN tie_counts tc ON t.name = tc.name
ORDER BY points DESC;

/******************************************************/

-- (iii)  Return the names of undefeated coaches (that is, coaches whose teams 
-- have lost no match). Output a table with a single column called ”coach”.

SELECT t.coach
FROM teams t
WHERE NOT EXISTS 
	(SELECT 1
	FROM all_winners w
    WHERE w.loser = t.name);

/******************************************************/
    
-- (iv)  Return the teams defeated only by the scoreboard leaders (i.e. ”if defeated, 
-- then the winner is a leader”). The leaders are the teams with the highest number 
-- of points (several leaders can be tied). Output a single column called ”name”.

CREATE VIEW scoreboard AS
-- same scoreboard as query (ii)
SELECT t.name, (2*h.home_wins + 3*a.away_wins + tc.ties) as points
FROM teams t LEFT JOIN home_win_counts h ON t.name = h.name
	LEFT JOIN away_win_counts a ON t.name = a.name
    LEFT JOIN tie_counts tc ON t.name = tc.name
ORDER BY points DESC;

-- teams defeated by scoreboard leader
SELECT w.loser AS name
FROM all_winners w, scoreboard s
WHERE w.winner = s.name and
	s.points = (SELECT max(s.points) FROM scoreboard s)
EXCEPT
-- teams defeated by non-scoreboard leader
SELECT w.loser AS name
FROM all_winners w, scoreboard s
WHERE w.winner = s.name and
	s.points < (SELECT max(s.points) FROM scoreboard s)
UNION
-- undefeated teams
SELECT t.name
FROM teams t
WHERE NOT EXISTS 
	(SELECT 1
	FROM all_winners w
    WHERE w.loser = t.name)
ORDER BY name;

/******************************************************/

-- (v) For each query in Problems (i) through (iv), create useful indexes or 
-- explain why there are none.

/*
For query (i), indices on hTeam and vTeam could be used to filter the matches
table to only include games involving the team of interest, if there were a 
sufficiently large number of teams.  In practice however, the league would 
likely never be large enough for such an index to be beneficial.

Queries (ii), (iii), and (iv) require a sequential scan of the entire matches 
table to identify winners and losers for each match, and would therefore not 
benefit from the addition of indices.

For the created scoreboard table used in question (vi), an index on name would
be useful to maintain the table upon changes to the matches table if there 
were enough teams, but again, having a large enough number of teams seems unlikely
in practice.
*/

/******************************************************/

-- (vi) Assume that the result of the query in Problem (ii) is materialized in 
-- a table called Scoreboard.  Write triggers to keep the Scoreboard up to date 
-- when the Matches table is inserted into, respectively updated. The resulting 
-- Scoreboard updates should be incremental (i.e. do not recompute Scoreboard 
-- from scratch).

-- create scoreboard table
CREATE TABLE scoreboard AS
SELECT t.name, (2*h.home_wins + 3*a.away_wins + tc.ties) as points
FROM teams t LEFT JOIN home_win_counts h ON t.name = h.name
	LEFT JOIN away_win_counts a ON t.name = a.name
    LEFT JOIN tie_counts tc ON t.name = tc.name
ORDER BY points DESC;

-- Below I create triggers to update the scoreboard table upon insertions, deletions, 
-- and updates to the matches table.  There are three triggers for insert, and three
-- triggers for delete, based on match outcome.  Updates to the match table activate 
-- both the delete and insert triggers, as the logic for updating a match is the 
-- same as first deleting the match and then inserting the updated match.

-- three triggers for insert (also activated by update) based on match outcome
-- 1) home team won the inserted match
CREATE TRIGGER scoreboard_insert_home_win
AFTER INSERT OR UPDATE ON matches
REFERENCING
	NEW ROW AS newmatch
FOR EACH ROW
WHEN newmatch.hscore > newmatch.vscore
	UPDATE scoreboard
	SET points = points + 2
	WHERE name = newmatch.hteam

-- 2) away team won the inserted match
CREATE TRIGGER scoreboard_insert_away_win
AFTER INSERT OR UPDATE ON matches
REFERENCING
	NEW ROW AS newmatch
FOR EACH ROW
WHEN newmatch.hscore < newmatch.vscore
	UPDATE scoreboard
	SET points = points + 3
	WHERE name = newmatch.vteam

-- 3) inserted match is a tie
CREATE TRIGGER scoreboard_insert_tie
AFTER INSERT OR UPDATE ON matches
REFERENCING
	NEW ROW AS newmatch
FOR EACH ROW
WHEN newmatch.hscore = newmatch.vscore
BEGIN
	UPDATE scoreboard
	SET points = points + 1
	WHERE name = newmatch.hteam;
	UPDATE scoreboard
	SET points = points + 1
	WHERE name = newmatch.vteam;
END;

-- three triggers for delete (also activated by update) based on match outcome
-- 1) home team won the deleted match
CREATE TRIGGER scoreboard_delete_home_win
AFTER DELETE OR UPDATE ON matches
REFERENCING
	OLD ROW AS oldmatch
FOR EACH ROW
WHEN oldmatch.hscore > oldmatch.vscore
	UPDATE scoreboard
	SET points = points - 2
	WHERE name = oldmatch.hteam

-- 2) away team won the deleted match
CREATE TRIGGER scoreboard_delete_away_win
AFTER DELETE OR UPDATE ON matches
REFERENCING
	OLD ROW AS oldmatch
FOR EACH ROW
WHEN oldmatch.hscore < oldmatch.vscore
	UPDATE scoreboard
	SET points = points - 3
	WHERE name = oldmatch.vteam

-- 3) deleted match was a tie
CREATE TRIGGER scoreboard_delete_tie
AFTER DELETE OR UPDATE ON matches
REFERENCING
	OLD ROW AS oldmatch
FOR EACH ROW
WHEN oldmatch.hscore = oldmatch.vscore
BEGIN
	UPDATE scoreboard
	SET points = points - 1
	WHERE name = oldmatch.hteam;
	UPDATE scoreboard
	SET points = points - 1
	WHERE name = oldmatch.vteam;
END;

	
/*
Below is a trigger implemented in postgreSQL to handle inserts, updates, 
and deletes to the matches table.  I included it because I had written 
it prior to reading on Piazza that we should write a SQL standard trigger 
and not use a postgres specific approach.
*/

-- delete existing table and trigger info
DROP TABLE IF EXISTS scoreboard CASCADE;
DROP TRIGGER IF EXISTS scoreboard_update ON matches CASCADE;
DROP FUNCTION IF EXISTS scoreboard_update();

-- trigger function to handle inserts, updates, deletes to match table
CREATE FUNCTION scoreboard_update() RETURNS trigger AS
$BODY$
BEGIN
	IF (TG_OP = 'DELETE') THEN
		-- if home team won, subtract 2 points from home team
		IF old.hscore > old.vscore THEN
			UPDATE scoreboard SET points = points - 2
			WHERE name = old.hteam;
		-- if visiting team won, subtract 3 points from visiting team
		ELSIF old.hscore < old.vscore THEN
			UPDATE scoreboard SET points = points - 3
			WHERE name = old.vteam;
		-- if tie, subtract 1 point from both teams
		ELSIF old.hscore = old.vscore THEN
			UPDATE scoreboard SET points = points - 1
			WHERE name = old.hteam;
			UPDATE scoreboard SET points = points - 1
			WHERE name = old.vteam;
		END IF;
 		RETURN OLD;
 		
 	ELSEIF (TG_OP = 'INSERT') THEN
 		-- if home team won, add 2 points to home team
		IF new.hscore > new.vscore THEN
			UPDATE scoreboard SET points = points + 2
			WHERE name = new.hteam;
		-- if visiting team won, add 3 points to visiting team
		ELSIF new.hscore < new.vscore THEN
			UPDATE scoreboard SET points = points + 3
			WHERE name = new.vteam;
		-- if tie, add 1 point to both teams
		ELSIF new.hscore = new.vscore THEN
			UPDATE scoreboard SET points = points + 1
			WHERE name = new.hteam;
			UPDATE scoreboard SET points = points + 1
			WHERE name = new.vteam;
		END IF;
	 	RETURN NEW;

	ELSIF (TG_OP = 'UPDATE') THEN
		-- perform deletion updates
		IF old.hscore > old.vscore THEN
			UPDATE scoreboard SET points = points - 2
			WHERE name = old.hteam;
		ELSIF old.hscore < old.vscore THEN
			UPDATE scoreboard SET points = points - 3
			WHERE name = old.vteam;
		ELSIF old.hscore = old.vscore THEN
			UPDATE scoreboard SET points = points - 1
			WHERE name = old.hteam;
			UPDATE scoreboard SET points = points - 1
			WHERE name = old.vteam;
		END IF;

		-- perform insertion updates
 		IF new.hscore > new.vscore THEN
			UPDATE scoreboard SET points = points + 2
			WHERE name = new.hteam;
		ELSIF new.hscore < new.vscore THEN
			UPDATE scoreboard SET points = points + 3
			WHERE name = new.vteam;
		ELSIF new.hscore = new.vscore THEN
			UPDATE scoreboard SET points = points + 1
			WHERE name = new.hteam;
			UPDATE scoreboard SET points = points + 1
			WHERE name = new.vteam;
		END IF;
	 	RETURN NEW;
	 END IF;
END;
$BODY$

LANGUAGE plpgsql;

-- create trigger to call trigger function
CREATE TRIGGER scoreboard_update
AFTER INSERT OR DELETE OR UPDATE ON matches
FOR EACH ROW
EXECUTE PROCEDURE scoreboard_update();