--------------------------------------------------------------------------------------------------------------------------
-- kpfOpsProcDrops.sql
--
-- Russ Laher (laher@ipac.caltech.edu)
--
-- 21 February 2023
--------------------------------------------------------------------------------------------------------------------------

DROP FUNCTION registerCalFile (
    startDate_           date,
    endDate_             date,
    level_               smallint,
    caltype_             character varying(32),
    object_              character varying(32),
    contentbits_         integer,
    nframes_             smallint,
    minmjd_              double precision,
    maxmjd_              double precision,
    infobits_            integer,
    filename_            character varying(255),
    checksum_            character varying(32),
    status_              smallint,
    createdBy_           character varying(32),
    created_             timestamp without time zone,
    comment_             character varying(255)
);

DROP FUNCTION getCalFile (
    obsDate_         date,
    level_           smallint,
    caltype_         character varying(32),
    object_          character varying(32),
    contentbitmask_  integer
);

-- Overloaded getCalFile function with additional maximum file-age parameter.
DROP FUNCTION getCalFile (
    obsDate_         date,
    level_           smallint,
    caltype_         character varying(32),
    object_          character varying(32),
    contentbitmask_  integer,
    maxage_          interval
);

DROP FUNCTION registerReadNoise (
    rId_           integer,
    rngreen1_      real,
    rngreen2_      real,
    rngreen3_      real,
    rngreen4_      real,
    rnred1_        real,
    rnred2_        real,
    rnred3_        real,
    rnred4_        real,
    rncahk_        real,
    greenreadtime_ real,
    redreadtime_   real,
    readspeed_     character varying(16)
);
