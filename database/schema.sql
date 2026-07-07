-- SHIRAYUME.EXE DATABASE

-- Drop the database if it exists (CAUTION: Data loss if no backups are made in advance!)
DROP DATABASE IF EXISTS shirayume_db;

-- Create database
CREATE DATABASE IF NOT EXISTS shirayume_db;

-- Run the following queries on shirayume_db
USE shirayume_db;

-- Initialize all the necessary tables
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    discriminator VARCHAR(4) NULL,
    avatar_url VARCHAR(2048) NULL,
    is_bot BOOLEAN DEFAULT FALSE NOT NULL,
    balance BIGINT DEFAULT 0 NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP() NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP()
        ON UPDATE CURRENT_TIMESTAMP()
        NOT NULL
);

CREATE TABLE guilds (
    guild_id BIGINT PRIMARY KEY,
    owner_id BIGINT NOT NULL,
    name VARCHAR(255) NOT NULL,
    icon_url VARCHAR(2048) NULL,
    member_count INT NOT NULL,
    bot_count INT NOT NULL,
    is_available BOOLEAN NOT NULL,
    economy_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    stats_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    stats_category_id BIGINT NULL,
    stats_channel_ids JSON NULL,
    base_message_reward INT DEFAULT 0 NOT NULL,
    currency VARCHAR(255) DEFAULT "Credits" NOT NULL,
    welcome_channel BIGINT NULL,
    leave_channel BIGINT NULL,
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP() NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP() NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP()
        ON UPDATE CURRENT_TIMESTAMP()
        NOT NULL,
    CONSTRAINT fk_guilds_userid_users_userid
        FOREIGN KEY (owner_id) REFERENCES users(user_id)
);

CREATE TABLE user_guild_settings (
    user_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP() NOT NULL,
    experience BIGINT DEFAULT 0 NOT NULL,
    level INT DEFAULT 0 NOT NULL,
    custom_title VARCHAR(255) NULL,
    last_xp_message_at DATETIME NULL,
    is_member BOOLEAN DEFAULT TRUE NOT NULL,
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP() NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP() NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP()
        ON UPDATE CURRENT_TIMESTAMP()
        NOT NULL,
    PRIMARY KEY (user_id, guild_id),
    CONSTRAINT fk_user_guild_settings_userid_users_userid
        FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT fk_user_guild_settings_guildid_guilds_guildid
        FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)
);

CREATE TABLE moderation_logs (
    mlog_id BIGINT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    moderator_id BIGINT NOT NULL,
    action_type ENUM(
        'warn',
        'mute',
        'kick',
        'ban',
        'unmute',
        'unban'
    ) DEFAULT 'warn' NOT NULL,
    reason TEXT NULL,
    action_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP() NOT NULL,
    duration_minutes INT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    pardoned BOOLEAN DEFAULT FALSE NOT NULL,
    CONSTRAINT fk_moderation_logs_guildid_guilds_guildid
        FOREIGN KEY (guild_id) REFERENCES guilds(guild_id),
    CONSTRAINT fk_moderation_logs_userid_users_userid
        FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT fk_moderation_logs_moderatorid_users_userid
        FOREIGN KEY (moderator_id) REFERENCES users(user_id)
);

CREATE TABLE polls (
    poll_id BIGINT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    creator_id BIGINT NOT NULL,
    question VARCHAR(255) NOT NULL,
    votes JSON NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP() NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP()
        ON UPDATE CURRENT_TIMESTAMP()
        NOT NULL,
    ends_at DATETIME NULL,
    CONSTRAINT fk_polls_guildid_guilds_guildid
        FOREIGN KEY (guild_id) REFERENCES guilds(guild_id),
    CONSTRAINT fk_polls_creatorid_users_userid
        FOREIGN KEY (creator_id) REFERENCES users(user_id)
);

CREATE TABLE user_economies (
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    local_balance BIGINT DEFAULT 0 NOT NULL,
    last_message_reward_time DATETIME NULL,
    PRIMARY KEY (guild_id, user_id),
    CONSTRAINT fk_usereconomy_guildid_guilds_guildid
        FOREIGN KEY (guild_id) REFERENCES guilds(guild_id),
	CONSTRAINT fk_user_economies_userid_users_userid
        FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE shop_items (
    item_id BIGINT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    name VARCHAR(64) NOT NULL,
    description VARCHAR(255) NOT NULL,
    price INT DEFAULT 0 NOT NULL,
    role_id BIGINT NULL,
    CONSTRAINT fk_shop_items_guildid_guilds_guildid
        FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)
);

CREATE TABLE global_shop_items (
    item_id BIGINT PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    description VARCHAR(255) NOT NULL,
    price INT DEFAULT 0 NOT NULL,
    item_type VARCHAR(32) NOT NULL,
    metadata JSON NOT NULL
);