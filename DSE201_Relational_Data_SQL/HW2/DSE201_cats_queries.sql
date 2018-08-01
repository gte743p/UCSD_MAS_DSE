-- "Overall Likes”: The Top-10 cat videos are the ones that have collected 
-- the highest numbers of likes, overall.
SELECT v.video_id, v.video_name, COUNT(l.video_id) as num_likes
FROM video v, likes l
WHERE l.video_id = v.video_id
GROUP BY v.video_id, v.video_name
ORDER BY num_likes DESC
LIMIT 10


-- “Friend Likes”: The Top-10 cat videos are the ones that have collected the highest 
-- numbers of likes from the friends of X.
WITH
user_X_id AS
(SELECT 1),

friends_of_X AS
(SELECT f.friend_id
FROM friend f
WHERE f.user_id = (SELECT * FROM user_X_id))

SELECT v.video_id, v.video_name, COUNT(l.video_id) as num_likes
FROM video v, likes l
WHERE l.video_id = v.video_id AND l.user_id IN
	(SELECT fX.friend_id
     FROM friends_of_X fX)
GROUP BY v.video_id, v.video_name
ORDER BY num_likes DESC
LIMIT 10


-- “Friends-of-Friends Likes”: The Top-10 cat videos are the ones that have collected 
-- the highest numbers of likes from friends and friends-of-friends.
WITH
user_X_id AS
(SELECT 1),

friends_of_X AS
(SELECT DISTINCT(f.friend_id)
FROM friend f
WHERE f.user_id = (SELECT * FROM user_X_id)),

friends_of_friends_of_X AS
(SELECT DISTINCT(f.friend_id)
FROM friend f
WHERE f.user_id IN
	(SELECT DISTINCT(fX.friend_id)
    FROM friends_of_X fX))

SELECT v.video_id, v.video_name, COUNT(l.video_id) as num_likes
FROM video v, likes l
WHERE l.video_id = v.video_id AND l.user_id IN
    (SELECT fX.friend_id
	FROM friends_of_X fX

    UNION

    SELECT ffX.friend_id
    FROM friends_of_friends_of_X ffX)
    
GROUP BY v.video_id, v.video_name
ORDER BY num_likes DESC
LIMIT 10


-- “My kind of cats”: The Top-10 cat videos are the ones that have collected the 
-- most likes from users who have liked at least one cat video that was liked by X.
WITH 
user_X_id AS
(SELECT 1),

liked_by_X AS
(SELECT v.video_id
FROM video v, likes l
WHERE l.user_id = (SELECT * FROM user_X_id) AND l.video_id = v.video_id)

SELECT v.video_id, v.video_name, SUM(l.video_id) as num_likes
FROM video v, likes l
WHERE l.video_id = v.video_id AND l.user_id IN
	(SELECT DISTINCT l.user_id
	FROM likes l
	WHERE l.video_id IN
		(SELECT x.video_id
		FROM liked_by_X x))
GROUP BY v.video_id, v.video_name
ORDER BY num_likes DESC
LIMIT 10


-- “My kind of cats – with preference (to cat aficionados that have the same tastes)”: 
-- The Top-10 cat videos are the ones that have collected the highest sum of weighted 
-- likes from every other user Y (i.e., given a cat video, each like on it, is 
-- multiplied by a weight).
WITH
user_X_id AS
(SELECT 1),

X_likes AS
(SELECT v_X.video_id, v_X.video_name
FROM video v_X, likes l_X
WHERE l_X.user_id = (SELECT * FROM user_X_id) AND l_X.video_id = v_X.video_id),

Y_likes AS
(SELECT l_Y.user_id, v_Y.video_id, v_Y.video_name
FROM video v_Y, likes l_Y
WHERE l_Y.user_id <> (SELECT * FROM user_X_id) AND l_Y.video_id = v_Y.video_id),

log_cos AS
(SELECT Y_likes.user_id, LOG(10, 1 + COUNT(*)) as adj_wt
FROM X_likes, Y_likes
WHERE X_likes.video_id = Y_likes.video_id
GROUP BY Y_likes.user_id),

other_likes AS
(SELECT v.video_id, v.video_name, l.user_id
FROM video v, likes l
WHERE l.video_id = v.video_id AND l.user_id <> (SELECT * FROM user_X_id))

SELECT other_likes.video_id, other_likes.video_name, SUM(log_cos.adj_wt) AS weighted_likes
FROM log_cos, other_likes
WHERE log_cos.user_id = other_likes.user_id
GROUP BY other_likes.video_id, other_likes.video_name
ORDER BY weighted_likes DESC
LIMIT 10