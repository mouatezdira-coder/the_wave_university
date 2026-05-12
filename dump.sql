CREATE TYPE statut_type AS ENUM ('private', 'public');


CREATE TABLE artist(
   idart serial primary key ,
   nom varchar(25) NOT NULL,
   prenom varchar(25) NOT NULL,
   nationA varchar(25),
   date_N date not null,
   date_M date check(date_M > date_N),
   constraint verification_age check(date_N <= CURRENT_DATE - INTERVAL '13 years')
);

CREATE TABLE groupe(
   idg serial primary key, 
   nomg varchar(25) NOT NULL,
   nationG varchar(25),
   date_crea date NOT NULL,
   genre varchar(25) NOT NULL
);

CREATE TABLE album(
   idal serial primary key ,
   titre varchar(100) not null ,
   description text,
   img_cov bytea,
   date_pari date NOT NULL
);

CREATE TABLE morceau(
   idm serial primary key ,
   titre varchar(25) NOT NULL,
   parole text,
   duree interval NOT NULL CHECK (duree > '00:00:00'),
   idg integer references groupe(idg) ON DELETE CASCADE,
   idal integer references album(idal) ON DELETE CASCADE,
   positionA int NOT NULL,
   url text not NULL,
   constraint unique_position_album UNIQUE(idal,positionA)
);

CREATE TABLE utilisateur(
   idu serial primary key,
   pseudo varchar(25) NOT NULL,
   email varchar(300) NOT NULL,
   mdp varchar(128) NOT NULL,
   date_IN date NOT NULL,
   CONSTRAINT unique_email UNIQUE (email),
   CONSTRAINT unique_pseudo UNIQUE (pseudo)
);

CREATE TABLE playlist(
   idp serial primary key ,
   titre varchar(100) NOT NULL,
   description text,
   statut statut_type NOT NULL, 
   idu integer references utilisateur(idu) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE contrat(
   idc serial primary key, 
   idart integer references artist(idart),
   idg integer references groupe(idg),
   role varchar(20) NOT NULL,
   date_entree date NOT NULL,
   date_sortie date NOT NULL check(date_sortie > date_entree)
);

CREATE TABLE appartient(
   idart integer references artist(idart) ON DELETE CASCADE,
   idg integer references groupe(idg) ON DELETE CASCADE,
   primary key(idart,idg)
);

CREATE TABLE participe(
   idm integer references morceau(idm) ON DELETE CASCADE,
   idart integer references artist(idart) ON DELETE CASCADE,
   role varchar(20) NOT NULL,
   primary key (idart,idm)
);

CREATE TABLE possede(
   idp integer references playlist(idp) on DELETE CASCADE,
   idm integer references morceau(idm) on DELETE CASCADE ,
   positionp int NOT NULL,
   primary key (idp,idm)
);

CREATE TABLE follow(
   idu integer references utilisateur(idu) ON DELETE CASCADE,
   idu2 integer references utilisateur(idu) ON DELETE CASCADE CHECK (idu2 <> idu),
   primary key (idu,idu2)
);

CREATE TABLE suit(
   idu integer references utilisateur(idu) ON DELETE CASCADE,
   idg integer references groupe(idg) ON DELETE CASCADE,
   primary key (idu,idg)
);

CREATE TABLE record_historique(
   idh serial primary key,
   historique timestamp with time zone NOT NULL,
   idm int references morceau(idm) ON DELETE CASCADE,
   idu int references utilisateur(idu) ON DELETE CASCADE,
   unique(idh,idu,idm)
);


INSERT INTO artist (nom, prenom, nationA, date_N) VALUES
('Smith', 'John', 'USA', '2000-05-15'),
('Johnson', 'Emily', 'UK', '1998-03-22'),
('Martinez', 'Carlos', 'Spain', '1995-11-30'),
('Kim', 'Ji-eun', 'South Korea', '2002-07-18'),
('Anderson', 'Michael', 'Canada', '1993-09-25'),
('Garcia', 'Sofia', 'Mexico', '2005-01-12'),
('Wong', 'David', 'China', '1997-06-28'),
('Dubois', 'Marie', 'France', '2003-04-15'),
('Yamamoto', 'Kenji', 'Japan', '1996-12-03'),
('Brown', 'Sarah', 'Australia', '2001-08-20'),
('Silva', 'Lucas', 'Brazil', '1999-02-14'),
('Mueller', 'Anna', 'Germany', '2004-10-07'),
('Rossi', 'Marco', 'Italy', '1994-07-31'),
('Kowalski', 'Adam', 'Poland', '2003-05-25'),
('Patel', 'Priya', 'India', '2006-03-18'),
('Lee', 'Min-ho', 'South Korea', '1998-12-09'),
('Taylor', 'James', 'UK', '1997-04-23'),
('Rodriguez', 'Isabella', 'Spain', '2002-09-16'),
('Chen', 'Wei', 'China', '2000-11-28'),
('Martin', 'Claire', 'France', '1995-06-11'),
('Tanaka', 'Yuki', 'Japan', '2004-01-05'),
('Wilson', 'Daniel', 'USA', '1996-08-14'),
('Santos', 'Ana', 'Portugal', '2001-03-27'),
('Schmidt', 'Lars', 'Germany', '1999-07-22'),
('Ferrari', 'Lucia', 'Italy', '2003-12-15'),
('Nowak', 'Eva', 'Poland', '1997-05-19'),
('Kumar', 'Raj', 'India', '2005-02-08'),
('Park', 'Sung-jin', 'South Korea', '1994-10-30'),
('Campbell', 'Emma', 'Canada', '2002-04-13'),
('Lopez', 'Miguel', 'Mexico', '1998-01-26');

INSERT INTO groupe (nomg, nationG, date_crea, genre) VALUES
('Stellar Dreams', 'USA', '2015-03-15', 'Pop Rock'),
('Electronic Pulse', 'UK', '2012-07-22', 'Electronic'),
('Global Harmony', 'South Korea', '2018-01-30', 'K-pop'),
('Metal Thunder', 'Germany', '2010-11-08', 'Metal'),
('Jazz Fusion', 'France', '2014-09-12', 'Jazz');

INSERT INTO album (titre, description, date_pari) VALUES
('Midnight Dreams', 'A journey through nocturnal soundscapes', '2020-06-15'),
('Electric Sky', 'Electronic fusion with modern beats', '2021-03-22'),
('Harmony Wave', 'K-pop meets global influences', '2022-01-10'),
('Thunder Road', 'Heavy metal anthology', '2019-11-30'),
('Jazz Chronicles', 'Modern jazz interpretations', '2021-07-18'),
('Summer Vibes', 'Feel-good summer hits', '2022-05-20'),
('Winter Tales', 'Cozy winter melodies', '2021-12-01'),
('Urban Stories', 'City life in music', '2022-03-15'),
('Nature''s Voice', 'Environmental inspirations', '2021-09-10'),
('Digital Age', 'Modern electronic fusion', '2022-06-30');

INSERT INTO morceau (titre, duree, idg, idal, positiona, url) VALUES
('Electric Dreams', '00:03:45', 1, 1, 1, 'audio/track1.mp3'),
('Midnight Rain', '00:04:12', 1, 1, 2, 'audio/track2.mp3'),
('Digital Love', '00:03:58', 2, 2, 1, 'audio/track3.mp3'),
('Neon Lights', '00:04:30', 2, 2, 2, 'audio/track4.mp3'),
('K-Pop Star', '00:03:15', 3, 3, 1, 'audio/track5.mp3'),
('Seoul Nights', '00:03:42', 3, 3, 2, 'audio/track6.mp3'),
('Metal Heart', '00:05:15', 4, 4, 1, 'audio/track7.mp3'),
('Thunder Strike', '00:04:48', 4, 4, 2, 'audio/track8.mp3'),
('Jazz Mood', '00:06:30', 5, 5, 1, 'audio/track9.mp3'),
('Smooth Saxophone', '00:05:45', 5, 5, 2, 'audio/track10.mp3'),
('Summer Breeze', '00:03:30', 1, 6, 1, 'audio/track11.mp3'),
('Beach Party', '00:03:55', 1, 6, 2, 'audio/track12.mp3'),
('Winter Morning', '00:04:20', 2, 7, 1, 'audio/track13.mp3'),
('Snow Dance', '00:04:15', 2, 7, 2, 'audio/track14.mp3'),
('City Lights', '00:03:40', 3, 8, 1, 'audio/track15.mp3'),
('Urban Beat', '00:03:50', 3, 8, 2, 'audio/track16.mp3'),
('Forest Dreams', '00:05:10', 4, 9, 1, 'audio/track17.mp3'),
('Ocean Waves', '00:04:35', 4, 9, 2, 'audio/track18.mp3'),
('Digital Mind', '00:03:45', 5, 10, 1, 'audio/track19.mp3'),
('Future Sound', '00:04:25', 5, 10, 2, 'audio/track20.mp3'),
('Morning Light', '00:03:55', 1, 1, 3, 'audio/track21.mp3'),
('Evening Star', '00:04:30', 2, 2, 3, 'audio/track22.mp3'),
('Dance All Night', '00:03:45', 3, 3, 3, 'audio/track23.mp3'),
('Heavy Dreams', '00:05:20', 4, 4, 3, 'audio/track24.mp3'),
('Jazz Evening', '00:06:15', 5, 5, 3, 'audio/track25.mp3');

INSERT INTO utilisateur (pseudo, email, mdp, date_IN) VALUES
('MusicLover', 'music.lover@email.com', 'SecurePass123', '2020-01-15'),
('RhythmKing', 'rhythm.king@email.com', 'Beats2022!', '2020-03-22'),
('SoundExplorer', 'sound.explorer@email.com', 'Explorer456', '2020-06-30'),
('MelodyMaster', 'melody.master@email.com', 'Melody789', '2020-09-18'),
('BeatMaker', 'beat.maker@email.com', 'BeatsRule123', '2020-12-05'),
('SongBird', 'song.bird@email.com', 'SingingStar!', '2021-02-14'),
('AudioPhile', 'audio.phile@email.com', 'Audio2022', '2021-04-23'),
('GrooveMaster', 'groove.master@email.com', 'Groove456!', '2021-07-11'),
('JamSession', 'jam.session@email.com', 'JamTime789', '2021-09-28'),
('SoundWave', 'sound.wave@email.com', 'WaveRider22', '2021-12-15'),
('MusicPro', 'music.pro@email.com', 'ProMusic123', '2022-01-30'),
('BeatBox', 'beat.box@email.com', 'BoxBeats456', '2022-03-18'),
('RhythmFlow', 'rhythm.flow@email.com', 'Flow789!', '2022-05-07'),
('MusicMind', 'music.mind@email.com', 'MindMusic22', '2022-06-25'),
('SoundMaster', 'sound.master@email.com', 'Master2022!', '2022-08-12');

INSERT INTO playlist (titre, description, statut, idu) VALUES
('Summer Vibes', 'Perfect playlist for summer days', 'public', 1),
('Chill Zone', 'Relaxing tunes for peaceful moments', 'public', 2),
('Party Mix', 'High energy dance tracks', 'public', 3),
('Road Trip', 'Best songs for long drives', 'private', 4),
('Workout Beats', 'Motivational music for exercise', 'public', 5),
('Late Night', 'Smooth songs for late hours', 'private', 6),
('Morning Coffee', 'Start your day right', 'public', 7),
('Study Session', 'Focus and concentration mix', 'private', 8),
('Weekend Mood', 'Fun tracks for the weekend', 'public', 9),
('Meditation', 'Calm and peaceful sounds', 'public', 10);

INSERT INTO contrat (idart, idg, role, date_entree, date_sortie) VALUES
(1, 1, 'Lead Vocalist', '2015-03-15', '2025-12-31'),
(2, 1, 'Guitarist', '2015-03-15', '2025-12-31'),
(3, 2, 'Producer', '2012-07-22', '2024-12-31'),
(4, 3, 'Lead Singer', '2018-01-30', '2026-12-31'),
(5, 3, 'Dancer', '2018-01-30', '2026-12-31'),
(6, 4, 'Lead Guitar', '2010-11-08', '2024-12-31'),
(7, 4, 'Drummer', '2010-11-08', '2024-12-31'),
(8, 5, 'Jazz Piano', '2014-09-12', '2025-12-31'),
(9, 5, 'Saxophone', '2014-09-12', '2025-12-31'),
(10, 1, 'Bassist', '2015-03-15', '2025-12-31'),
(11, 2, 'DJ', '2012-07-22', '2024-12-31'),
(12, 3, 'Choreographer', '2018-01-30', '2026-12-31'),
(13, 4, 'Bass Guitar', '2010-11-08', '2024-12-31'),
(14, 5, 'Trumpet', '2014-09-12', '2025-12-31'),
(15, 1, 'Drummer', '2015-03-15', '2025-12-31');

INSERT INTO appartient (idart, idg) VALUES
(1, 1), (2, 1), (3, 2), (4, 3), (5, 3),
(6, 4), (7, 4), (8, 5), (9, 5), (10, 1),
(11, 2), (12, 3), (13, 4), (14, 5), (15, 1);

INSERT INTO participe (idm, idart, role) VALUES
(1, 1, 'Lead Vocals'),
(1, 2, 'Guitar'),
(2, 1, 'Lead Vocals'),
(3, 3, 'Producer'),
(4, 3, 'Producer'),
(5, 4, 'Lead Vocals'),
(6, 4, 'Lead Vocals'),
(7, 6, 'Lead Guitar'),
(8, 6, 'Lead Guitar'),
(9, 8, 'Piano'),
(10, 9, 'Saxophone');

INSERT INTO possede (idp, idm, positionp) VALUES
(1, 1, 1), (1, 2, 2), (1, 3, 3), (1, 4, 4),
(2, 5, 1), (2, 6, 2), (2, 7, 3),
(3, 8, 1), (3, 9, 2), (3, 10, 3),
(4, 11, 1), (4, 12, 2), (4, 13, 3),
(5, 14, 1), (5, 15, 2), (5, 16, 3);

INSERT INTO follow (idu, idu2) VALUES
(1, 2), (1, 3), (2, 1), (2, 4), (3, 1),
(3, 2), (4, 1), (4, 2), (5, 1), (5, 2);

INSERT INTO suit (idu, idg) VALUES
(1, 1), (1, 2), (2, 1), (2, 3), (3, 4),
(3, 5), (4, 1), (4, 2), (5, 3), (5, 4);

INSERT INTO record_historique (historique, idm, idu) VALUES
('2023-11-09 07:30:00+00', 1, 1),
('2023-11-09 07:45:00+00', 2, 1),
('2023-11-09 08:15:00+00', 3, 1),
('2023-11-09 19:20:00+00', 1, 1),
('2023-11-09 19:45:00+00', 4, 1),
('2023-11-09 20:10:00+00', 5, 1),
('2023-11-09 14:00:00+00', 6, 2),
('2023-11-09 14:25:00+00', 7, 2),
('2023-11-09 14:50:00+00', 8, 2),
('2023-11-09 15:15:00+00', 6, 2),
('2023-11-09 15:40:00+00', 9, 2),
('2023-11-09 22:00:00+00', 10, 3),
('2023-11-09 22:25:00+00', 11, 3),
('2023-11-09 22:50:00+00', 12, 3),
('2023-11-09 23:15:00+00', 10, 3),
('2023-11-09 23:40:00+00', 11, 3),
('2023-11-09 06:00:00+00', 13, 4),
('2023-11-09 06:25:00+00', 14, 4),
('2023-11-09 06:50:00+00', 15, 4),
('2023-11-09 17:00:00+00', 13, 4),
('2023-11-09 17:25:00+00', 16, 4),
('2023-11-09 09:00:00+00', 17, 5),
('2023-11-09 09:30:00+00', 18, 5),
('2023-11-09 10:00:00+00', 19, 5),
('2023-11-09 10:30:00+00', 17, 5),
('2023-11-09 11:00:00+00', 20, 5),
('2023-11-09 12:00:00+00', 21, 1),
('2023-11-09 13:30:00+00', 22, 2),
('2023-11-09 16:45:00+00', 23, 3),
('2023-11-09 18:15:00+00', 24, 4),
('2023-11-09 20:30:00+00', 25, 5);



CREATE VIEW nb_ecoutes AS 
SELECT 
   idm,
   TO_CHAR(historique, 'YYYY-MM') AS mois,
   COUNT(idu) AS total_ecoutes
FROM record_historique 
GROUP BY idm, mois
ORDER BY mois DESC, total_ecoutes DESC;

CREATE VIEW nb_personne_ecoute AS 
SELECT 
   idm,
   TO_CHAR(historique, 'YYYY-MM') AS mois,
   COUNT(DISTINCT idu) AS nb_personne
FROM record_historique 
GROUP BY idm, mois;

CREATE VIEW nb_partages AS
SELECT 
   idm,
   COUNT(idp) AS nb_partage 
FROM possede 
NATURAL JOIN playlist 
WHERE statut ='public'
GROUP BY idm;

CREATE VIEW revenue_groupes AS 
SELECT 
   idg,
   TO_CHAR(historique, 'YYYY-MM') AS mois,
   (COUNT(DISTINCT(idu, idm)) * 0.10 + 0.01 * (COUNT(idu) - COUNT(DISTINCT(idu, idm)))) AS revenue 
FROM morceau 
NATURAL JOIN record_historique 
GROUP BY idg, mois
ORDER BY mois DESC, revenue DESC;