import { CommandoMessage } from 'discord.js-commando';
import { Command } from '../../';
import ModmailBot from '../../../bot';
import { LogUtil } from '../../../util';

type Args = {
  msgID?: string;
}

export default class Delete extends Command {
  constructor(client: ModmailBot) {
    super(client, {
      name: 'delete',
      aliases: ['d', 'remove'],
      description: 'Delete a message',
      group: 'messages',
      memberName: 'delete',
      guildOnly: true,
      args: [
        {
          key: 'messageID',
          prompt: 'The ID of the message to delete',
          type: 'string',
          default: '',
        },
      ],
    });
  }

  public async run(msg: CommandoMessage, { msgID }: Args): Promise<null> {
    const modmail = ModmailBot.getModmail();
    const thread = await modmail.threads.getByChannel(msg.channel.id);

    if (thread === null) {
      const res = 'Not currently in a thread..';
      LogUtil.cmdWarn(msg, res);
      await msg.say(res);
      return null;
    }

    if (msgID !== undefined) {
      await thread.deleteMsg(msgID);
    } else {
      await thread.deleteLastMsg(msg.author.id);
    }

    await msg.react('✅');

    return null;
  }
}