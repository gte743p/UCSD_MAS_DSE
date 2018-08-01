SQL_create_events_table = '''DROP TABLE IF EXISTS events;
                            DROP TABLE IF EXISTS events_dictionary;

							CREATE TABLE public.events
							(
    							id serial NOT NULL,
    							event_title character varying(50) COLLATE pg_catalog."default",
    							event_id integer,
    							event_subtitle character varying(25) COLLATE pg_catalog."default",
    							event_type character varying(10) COLLATE pg_catalog."default",
    							event_desc character varying(512) COLLATE pg_catalog."default",
    							event_loc character varying(512) COLLATE pg_catalog."default",
    							event_start character varying(25) COLLATE pg_catalog."default",
    							event_end character varying(25) COLLATE pg_catalog."default",
    							exp_attendance character varying(25) COLLATE pg_catalog."default",
    							exp_participants character varying(10) COLLATE pg_catalog."default",
    							event_host character varying(50) COLLATE pg_catalog."default",
    							event_url character varying(128) COLLATE pg_catalog."default",
    							event_address character varying(50) COLLATE pg_catalog."default",
    							latitude double precision,
    							longitude double precision
							)
							WITH (
    							OIDS = FALSE
							)
							TABLESPACE pg_default;

							ALTER TABLE public.events
    							OWNER to postgres;
                            

                            CREATE TABLE public.events_dictionary
                            (
                            id serial NOT NULL,
                            field character varying(25),
                            description character varying(50),
                            possible_values character varying(50)
                            );

                            COPY events (event_title,event_id,event_subtitle,event_type,event_desc,event_loc,event_start,event_end,exp_attendance,exp_participants,event_host,event_url,event_address,latitude,longitude)
                            FROM '{0}special_events_list_datasd.csv' DELIMITER ',' CSV HEADER;

                            COPY events_dictionary (field,description,possible_values)
                            FROM '{0}special_events_listings_dictionary.csv' DELIMITER ',' CSV HEADER; 
							
                            ALTER TABLE events DROP COLUMN IF EXISTS geom;
                            ALTER TABLE events ADD COLUMN geom geometry;
                            UPDATE events SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326);'''.format(filepath)


SQL_update_segments = '''ALTER TABLE segments DROP COLUMN IF EXISTS geom;
                        ALTER TABLE segments DROP COLUMN IF EXISTS seg_length;
                        ALTER TABLE segments DROP COLUMN IF EXISTS direction;
                        ALTER TABLE segments ADD COLUMN geom geometry;
                        ALTER TABLE segments ADD COLUMN seg_length double precision;
                        ALTER TABLE segments ADD COLUMN direction integer;
                        UPDATE segments SET geom = st_makeline(st_makepoint(lon1,lat1),st_makepoint(lon2,lat2));
                        UPDATE segments SET seg_length = ST_Length(geom);
                        
                        UPDATE segments set direction = 1 where degrees(st_azimuth(st_point(lon1,lat1),st_point(lon2,lat2))) > 315 AND degrees(st_azimuth(st_point(lon1,lat1),st_point(lon2,lat2))) <= 45;
                        UPDATE segments set direction = 2 where degrees(st_azimuth(st_point(lon1,lat1),st_point(lon2,lat2))) > 45 AND degrees(st_azimuth(st_point(lon1,lat1),st_point(lon2,lat2))) <= 135;
                        UPDATE segments set direction = 3 where degrees(st_azimuth(st_point(lon1,lat1),st_point(lon2,lat2))) > 135 AND degrees(st_azimuth(st_point(lon1,lat1),st_point(lon2,lat2))) <= 225;
                        UPDATE segments set direction = 4 where degrees(st_azimuth(st_point(lon1,lat1),st_point(lon2,lat2))) > 225 AND degrees(st_azimuth(st_point(lon1,lat1),st_point(lon2,lat2))) <= 315;'''



SQL_Time_Bucketing = '''DROP TABLE IF EXISTS time_{0};

						CREATE TABLE public.time_{0} AS 
                        (
                        SELECT DISTINCT 
                            date, 
                            day_of_week, 
                            month, 
                            is_weekend, 
                            is_holiday, 
                            is_rushhour,
                            (date_trunc('hour', time) + date_part('minute', time)::int / {0} * interval '{0} min')::time as time,
                            (date_trunc('hour', timestamp_round) + date_part('minute', timestamp_round)::int / {0} * interval '{0} min')::timestamp as timestamp_round
                        FROM time
                        );

                        ALTER TABLE time_{0} ADD COLUMN time_id SERIAL;

                        ALTER TABLE time_{0} ADD PRIMARY KEY (time_id);


                        DROP VIEW IF EXISTS v_time_{0};

                        CREATE VIEW v_time_{0} as 
                        (
                            select  date,
                            		day_of_week,
                            		month,
                            		is_weekend, 
                                    is_holiday, 
                                    is_rushhour,
                                    time,
                            		timestamp_round,
                                    time_id
                            from time_{0}
                        );

                        CREATE TABLE time_{0}a AS 
                        (
                            select  date,
                            		day_of_week,
                            		month,
                            		is_weekend, 
                                    is_holiday, 
                                    is_rushhour,
                                    time,
                            		timestamp_round,
                                    time_id
                            from    v_time_{0}
                        );


                        DROP VIEW v_time_{0};

                        DROP TABLE time_{0};

                        ALTER TABLE time_{0}a RENAME TO time_{0};
                        
                        
                        DROP TABLE IF EXISTS matrix_{0};
                            CREATE TABLE matrix_{0} as (
                                with time_id_map as (
                                    select  time_{0}.time_id as new_time_id, 
                                        time.time_id as orig_time_id 
                                    from    time_{0}, time
                                    where   time_{0}.timestamp_round = (
                                        date_trunc('hour', time.timestamp_round) + 
                                        date_part('minute', time.timestamp_round)::int / {0} * interval '{0} min' )::timestamp
                            )

                            select  m.uuid_instance_id, m.path, m.segment_id, time_id_map.new_time_id as time_id
                            from    matrix m, time_id_map
                            where   m.time_id = time_id_map.orig_time_id)'''.format(time_bucket)
                            
SQL_create_segments_times_selected = '''DROP TABLE IF EXISTS public.segments_selected;
										CREATE TABLE public.segments_selected
										(
    										lat1 double precision,
    										lon1 double precision,
    										lat2 double precision,
    										lon2 double precision,
    										segment_id integer,
    										street character varying(50) COLLATE pg_catalog."default",
    										city character varying(50) COLLATE pg_catalog."default",
    										road_type integer,
    										geom geometry,
    										direction integer,
    										seg_length double precision
											)
										WITH (
    										OIDS = FALSE
										)
										TABLESPACE pg_default;

										ALTER TABLE public.segments_selected
    										OWNER to postgres;
    							
									DROP TABLE IF EXISTS public.times_selected;

									CREATE TABLE public.times_selected
									(
    									date date,
    									day_of_week character varying COLLATE pg_catalog."default",
    									month character varying COLLATE pg_catalog."default",
    									is_weekend boolean,
    									is_holiday boolean,
    									is_rushhour boolean,
    									"time" time without time zone,
    									timestamp_round timestamp without time zone,
    									time_id integer
										)
										WITH (
    										OIDS = FALSE
										)
										TABLESPACE pg_default;

										ALTER TABLE public.times_selected
    										OWNER to postgres;'''

SQL_drop_indexes = '''ALTER TABLE segments DROP COLUMN IF EXISTS index;
					ALTER TABLE time DROP COLUMN IF EXISTS index;
					ALTER TABLE uuid DROP COLUMN IF EXISTS index;
					ALTER TABLE matrix DROP COLUMN IF EXISTS index;'''
					
					
SQL_pct_segments = '''
					drop table if exists seg_cum_pct;
					
					create table seg_cum_pct as
					(with all_segments as
					(select s.segment_id, count(m.time_id) as num_timestamps
					from matrix m, time t, segments s
					where m.time_id = t.time_id and s.segment_id = m.segment_id
					group by s.segment_id
					order by num_timestamps desc),

					seg_counts as
					(select num_timestamps, count(*) as seg_count
					from all_segments
					group by num_timestamps),

					cum_seg_count as
					(select num_timestamps, seg_count, sum(seg_count)
					over (order by seg_count desc)
					from seg_counts
					order by sum asc),

					seg_count_total as
					(select sum(seg_count) as total_segments from cum_seg_count),

					cum_seg_pct_table as
					(select csc.num_timestamps, csc.seg_count, csc.sum, csc.sum / sct.total_segments as cum_seg_pct
					from cum_seg_count as csc, seg_count_total as sct)

					select all_segments.segment_id, round(cum_seg_pct_table.cum_seg_pct, {}) as cum_seg_pct
					from all_segments, cum_seg_pct_table
					where all_segments.num_timestamps = cum_seg_pct_table.num_timestamps
					order by cum_seg_pct asc);
					
					alter table segments
					add column cum_seg_pct numeric;
					
					update segments
					set cum_seg_pct = seg_cum_pct.cum_seg_pct
					from seg_cum_pct
					where seg_cum_pct.segment_id = segments.segment_id;
					'''.format(cum_seg)

SQL_pct_time = '''drop table if exists ts_cum_pct;

				create table ts_cum_pct as
				(with all_ts as
				(select t.time_id, count(s.segment_id) as num_segments
				from matrix m, time t, segments s
				where m.time_id = t.time_id and s.segment_id = m.segment_id
				group by t.time_id
				order by num_segments desc),

				ts_counts as
				(select num_segments, count(*) as ts_count
				from all_ts
				group by num_segments),

				cum_ts_count as
				(select num_segments, ts_count, sum(ts_count)
				over (order by ts_count desc)
				from ts_counts
				order by sum asc),

				ts_count_total as
				(select sum(ts_count) as total_ts from cum_ts_count),

				cum_ts_pct_table as
				(select csc.num_segments, csc.ts_count, csc.sum, csc.sum / sct.total_ts as cum_ts_pct
				from cum_ts_count as csc, ts_count_total as sct)

				select all_ts.time_id, round(cum_ts_pct_table.cum_ts_pct*100, {}) as cum_ts_pct
				from all_ts, cum_ts_pct_table
				where all_ts.num_segments = cum_ts_pct_table.num_segments
				order by cum_ts_pct asc);
				
				alter table time
				add column cum_ts_pct numeric;
				
				update time
				set cum_ts_pct = ts_cum_pct.cum_ts_pct
				from ts_cum_pct
				where ts_cum_pct.time_id = time.time_id;
				
				update time
				set cum_ts_pct = 0
				where cum_ts_pct is null;'''.format(cum_ts)