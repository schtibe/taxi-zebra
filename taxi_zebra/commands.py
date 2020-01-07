import colorama
import datetime

import click

from taxi.commands.base import cli, get_timesheet_collection_for_context
from taxi.plugins import plugins_registry

from .backend import ZebraBackend


def hours_to_days(hours):
    """
    Convert the given amount of hours to a 2-tuple `(days, hours)`.
    """
    days = int(hours // 8)
    hours_left = hours % 8

    return days, hours_left


@cli.group()
def zebra():
    """
    Zebra-related commands.
    """
    pass


def signed_number(number, precision=2):
    """
    Return the given number as a string with a sign in front of it, ie. `+` if the number is positive, `-` otherwise.
    """
    prefix = '' if number <= 0 else '+'
    number_str = '{}{:.{precision}f}'.format(prefix, number, precision=precision)

    return number_str


def get_first_dow(date):
    """
    Return the first day of the week for the given date.
    """
    return date - datetime.timedelta(days=date.weekday())


def get_last_dow(date):
    """
    Return the last day of the week for the given date.
    """
    return date + datetime.timedelta(days=(6 - date.weekday()))


@zebra.command()
@click.pass_context
def balance(ctx):
    """
    Show Zebra balance.

    Like the hours balance, vacation left, etc.
    """
    backend = plugins_registry.get_backends_by_class(ZebraBackend)[0]

    timesheet_collection = get_timesheet_collection_for_context(ctx, None)
    hours_to_be_pushed = timesheet_collection.get_hours(pushed=False, ignored=False, unmapped=False)

    today = datetime.date.today()

    user_info = backend.get_user_info()
    timesheets_week = backend.get_timesheets(get_first_dow(today), get_last_dow(today))
    timesheets_today = backend.get_timesheets(today, today)
    total_duration_week = sum([float(timesheet['time']) for timesheet in timesheets_week])
    total_duration_today = sum([float(timesheet['time']) for timesheet in timesheets_today])

    vacation = hours_to_days(user_info['vacation']['difference'])
    vacation_balance = '{} days, {:.2f} hours'.format(*vacation)

    hours_balance = user_info['hours']['hours']['balance']
    hours_balance_after_push = hours_balance = + hours_to_be_pushed

    def colored_output(value, threshold, str_value=None):
        if str_value is None:
            str_value = value

        if value > threshold:
            color = colorama.Fore.GREEN
        elif value < threshold:
            color = colorama.Fore.RED
        else:
            color = colorama.Fore.YELLOW

        return {
            "color": color,
            "value": str_value,
            "reset": colorama.Fore.RESET
        }

    click.echo("Hours balance: {color}{value}{reset}".format(**colored_output(
        hours_balance, 0, signed_number(hours_balance))))

    click.echo("Hours balance after push: {color}{value}{reset}".format(
        **colored_output(hours_balance_after_push, 0, signed_number(hours_balance_after_push))))

    click.echo("Hours done this week: {color}{value:.2f}{reset}".format(
        **colored_output(total_duration_week, 40)
    ))

    click.echo("Hours done today: {color}{value:.2f}{reset}".format(
        **colored_output(total_duration_today, 8)
    ))
    click.echo("Hours to be pushed: {:.2f}".format(hours_to_be_pushed))
    click.echo("Vacation left: {}".format(vacation_balance))
