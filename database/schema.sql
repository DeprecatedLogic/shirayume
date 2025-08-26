-- SHIRAYUME.EXE DATABASE

-- Drop the database if it exists (CAUTION: Data loss if no backups are made in advance!)
DROP DATABASE shirayume_db;

-- Create database
CREATE DATABASE IF NOT EXISTS shirayume_db;

-- Run the following queries on shirayume_db
USE shirayume_db;

-- Initialize all the necessary tables
CREATE TABLE users (
    user_id BIGINT UNSIGNED primary key,
    username VARCHAR(255) not null,
    discriminator VARCHAR(4) null,
    avatar_url VARCHAR(2048) null,
    is_bot BOOLEAN DEFAULT false not null,
    currency BIGINT DEFAULT 0 not null,
    created_at DATETIME DEFAULT current_timestamp not null,
    updated_at DATETIME DEFAULT current_timestamp not null
        ON UPDATE current_timestamp
        not null
);

CREATE TABLE guilds (
    guild_id BIGINT UNSIGNED primary key,
    owner_id BIGINT UNSIGNED not null,
    name VARCHAR(255) not null,
    icon_url VARCHAR(2048) null,
    member_count INT not null,
    bot_count INT not null,
    is_available BOOLEAN not null,
    welcome_channel BIGINT UNSIGNED null,
    joined_at DATETIME DEFAULT current_timestamp not null,
    created_at DATETIME DEFAULT current_timestamp not null,
    updated_at DATETIME DEFAULT current_timestamp
        ON UPDATE current_timestamp
        not null,
    constraint fk_guilds_userid_users_userid
        foreign key (user_id) references users(user_id)
);

CREATE TABLE user_guild_settings (
    user_id BIGINT UNSIGNED not null,
    guild_id BIGINT UNSIGNED not null,
    last_interaction DATETIME DEFAULT current_timestamp not null,
    experience BIGINT UNSIGNED DEFAULT 0 not null,
    level INT UNSIGNED DEFAULT 0 not null,
    custom_title VARCHAR(255) null,
    last_xp_message_at DATETIME null,
    is_member BOOLEAN DEFAULT true not null,
    joined_at DATETIME DEFAULT current_timestamp not null,
    created_at DATETIME DEFAULT current_timestamp not null,
    updated_at DATETIME DEFAULT current_timestamp
        ON UPDATE current_timestamp
        not null,
    primary key (user_id, guild_id),
    constraint fk_user_guild_settings_userid_users_userid
        foreign key (user_id) references users(user_id),
    constraint fk_user_guild_settings_guildid_guilds_guildid
        foreign key (guild_id) references guilds(guild_id)
);

CREATE TABLE moderation_logs (
    mlog_id BIGINT UNSIGNED primary key,
    guild_id BIGINT UNSIGNED not null,
    user_id BIGINT UNSIGNED not null,
    moderator_id BIGINT UNSIGNED not null,
    action_type ENUM(
        'warn',
        'mute',
        'kick',
        'ban',
        'unmute',
        'unban'
    ) DEFAULT 'warn' not null,
    reason TEXT null,
    action_timestamp DATETIME DEFAULT current_timestamp not null,
    duration_minutes INT null,
    is_active BOOLEAN DEFAULT true,
    pardoned BOOLEAN DEFAULT false,
    constraint fk_moderation_logs_guildid_guilds_guildid
        foreign key (guild_id) references guilds(guild_id),
    constraint fk_moderation_logs_userid_users_userid
        foreign key (user_id) references users(user_id),
    constraint fk_moderation_logs_moderatorid_users_userid
        foreign key (moderator_id) references users(user_id)
);
