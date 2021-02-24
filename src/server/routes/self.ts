import {
  Response,
  Router,
} from 'express';
import ModmailServer from '../server';
import Route from './route';
import { RequestWithUser } from '../models/types';


export default class SelfRoute extends Route {
  constructor(mm: ModmailServer) {
    const router = Router();
    super(mm, 'self', router);
  }

  public getRouter(): Router {
    this.router.get('/', this.root.bind(this));

    return this.router;
  }

  private async root(req: RequestWithUser, res: Response) {
    const logger = this.getLogger();
    let { user } = req.session;

    if (!user) {
      res.status(403);
      res.end();
      return;
    }

    try {
      res.json(user);
    } catch (err) {
      logger.error(err);
      res.status(500);
    } finally {
      res.end();
    }
  }
}