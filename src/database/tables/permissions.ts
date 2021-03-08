import { Role } from '@newcircuit/modmail-types';
import { DBRole } from '../models/types';
import { Pool } from 'pg';
import * as PermUtil from '../util/PermUtil';
import Table from '../models/table';

export default class PermissionsTable extends Table {
  constructor(pool: Pool) {
    super(pool, 'permissions');
  }

  /**
   * Add a new role for a certain category.
   * @param {Role} role
   * @returns {Promise<boolean>} Whether it was added or not
   */
  public async add(role: Role): Promise<boolean> {
    const client = await this.getClient();
    const level = PermUtil.resolve(role.level);
    const res = await client.query(
      `INSERT INTO modmail.permissions (category_id, role_id, level)
       VALUES ($1, $2, $3);`,
      [role.category, role.roleID, level],
    );

    return res.rowCount !== 0;
  }

  /**
   * Remove a role. We don't need to intake the category because all role ID's
   * are unique and two categories can't have the same role ID.
   * @param {string} id
   * @returns {Promise<boolean>} Whether it was removed or not
   */
  public async remove(id: string): Promise<boolean> {
    const client = await this.getClient();
    const res = await client.query(
      `DELETE
       FROM modmail.permissions
       WHERE role_id = $1;`,
      [id],
    );

    return res.rowCount !== 0;
  }

  public async fetch(roleID: string): Promise<Role | null> {
    const client = await this.getClient();
    const res = await client.query(
      `SELECT *
       FROM modmail.permissions
       WHERE role_id = $1;`,
      [roleID],
    );

    if (res.rowCount === 0) {
      return null;
    }

    return PermissionsTable.parse(res.rows[0]);
  }

  public async fetchFrom(roleIDs: string[]): Promise<Role[]> {
    const client = await this.getClient();
    const res = await client.query(
      `SELECT *
       FROM modmail.permissions
       WHERE role_id = ANY ($1);`,
      [roleIDs],
    );

    return res.rows.map((role) => PermissionsTable.parse(role));
  }

  public async fetchAll(category: string): Promise<Role[]> {
    const client = await this.getClient();
    const res = await client.query(
      `SELECT *
       FROM modmail.permissions
       WHERE category_id = $1;`,
      [category],
    );

    return res.rows.map(PermissionsTable.parse);
  }

  /**
   * Initialize the permissions table
   */
  protected async init(): Promise<void> {
    const client = await this.getClient();
    await client.query(
      `CREATE TABLE IF NOT EXISTS modmail.permissions
       (
           category_id BIGINT                                                 NOT NULL
               references modmail.categories,
           role_id     TEXT UNIQUE                                            NOT NULL,
           level       modmail.role_level DEFAULT \'mod\'::modmail.role_level NOT NULL
       )`
    );

    await client.query(
      `CREATE UNIQUE INDEX IF NOT EXISTS permissions_role_id_uindex on modmail.permissions (role_id)`,
    );
  }

  private static parse(role: DBRole): Role {
    return {
      category: role.category_id.toString(),
      roleID: role.role_id.toString(),
      level: PermUtil.resolveStr(role.level),
    };
  }
}
