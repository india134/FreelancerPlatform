# forms.py

from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SubmitField,
    TextAreaField, DecimalField, IntegerField, SelectField,
    RadioField, FieldList, FormField
)
from wtforms.fields import EmailField, DateField, URLField
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length,
    URL, NumberRange, Optional
)


class CSRFOnlyForm(FlaskForm):
    """Use this on routes that only need to render/protect a CSRF token."""
    pass


class FreelancerRegistrationForm(FlaskForm):
    name            = StringField(
        'Full Name',
        validators=[DataRequired(), Length(max=100)]
    )
    email           = EmailField(
        'Email Address',
        validators=[DataRequired(), Email(), Length(max=120)]
    )
    password        = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6)]
    )
    confirm_password= PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match')
        ]
    )
    agree           = BooleanField(
        'I agree to the Terms of Service and Privacy Policy',
        validators=[DataRequired()]
    )
    submit          = SubmitField('Create Account')


class LoginForm(FlaskForm):
    email    = EmailField(
        'Email Address',
        validators=[DataRequired(), Email(), Length(max=120)]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired()]
    )
    remember = BooleanField('Remember Me')
    submit   = SubmitField('Log In')


class ClientForm(FlaskForm):
    name      = StringField(
        'Client Name',
        validators=[DataRequired(), Length(max=100)]
    )
    email     = EmailField(
        'Email Address',
        validators=[Optional(), Email(), Length(max=120)]
    )
    phone     = StringField(
        'Phone',
        validators=[Optional(), Length(max=20)]
    )
    notes     = TextAreaField(
        'Notes',
        validators=[Optional(), Length(max=500)]
    )
    meeting_link = StringField(
        "Default Meeting Link",
        validators=[Optional(), URL(message="Must be a valid URL")])
    submit    = SubmitField('Save Client')


class ProjectForm(FlaskForm):
    title       = StringField(
        'Project Title',
        validators=[DataRequired(), Length(max=150)]
    )
    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=1000)]
    )
    start_date  = DateField(
        'Start Date',
        format='%Y-%m-%d',
        validators=[Optional()]
    )
    end_date    = DateField(
        'End Date',
        format='%Y-%m-%d',
        validators=[Optional()]
    )
    currency    = StringField(
        'Currency',
        validators=[Optional(), Length(max=10)]
    )
    status      = SelectField(
        'Status',
        choices=[
            ('pending','Pending'),
            ('active','Active'),
            ('completed','Completed'),
            ('archived','Archived')
        ],
        default='pending'
    )
    submit      = SubmitField('Save Project')


class ProfileForm(FlaskForm):
    name       = StringField(
        'Full Name',
        render_kw={'readonly': True}
    )
    email      = EmailField(
        'Email Address',
        render_kw={'readonly': True}
    )
    education  = TextAreaField(
        'Education',
        validators=[Optional(), Length(max=500)]
    )
    experience = TextAreaField(
        'Experience',
        validators=[Optional(), Length(max=1000)]
    )
    linkedin   = URLField(
        'LinkedIn URL',
        validators=[Optional(), URL(), Length(max=200)]
    )
    submit     = SubmitField('Save Profile')


#
#  PRICING PROPOSAL & STAGE FORMS
#

class PricingStageForm(FlaskForm):
    """One row of the multi‐stage proposal form."""
    class Meta:
        csrf = False   # disable CSRF on nested subforms

    tech_details   = StringField(
        'Tech Details',
        validators=[Optional(), Length(max=200)]
    )
    deliverables   = TextAreaField(
        'Deliverables',
        validators=[Optional(), Length(max=1000)]
    )
    amount         = DecimalField(
        'Amount (fixed only)',
        places=2,
        validators=[Optional(), NumberRange(min=0)]
    )
    hours          = IntegerField(
        'Hours (hourly only)',
        validators=[Optional(), NumberRange(min=0)]
    )
    due_date       = DateField(
        'Due Date',
        format='%Y-%m-%d',
        validators=[Optional()]
    )
    work_status    = SelectField(
        'Work Status',
        choices=[('pending','Pending'),('done','Done')],
        default='pending'
    )
    payment_status = SelectField(
        'Payment Status',
        choices=[('pending','Pending'),('paid','Paid')],
        default='pending'
    )


class PricingProposalForm(FlaskForm):
    """The top‐level proposal form, with a dynamic FieldList of stages."""
    type             = RadioField(
        'Proposal Type',
        choices=[('fixed','Fixed Price'),('hourly','Hourly Rate')],
        default='fixed',
        validators=[DataRequired()]
    )
    total_charge     = DecimalField(
        'Total Charge (fixed only)',
        places=2,
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'placeholder': 'e.g. 15000.00'}
    )
    advanced_payment = DecimalField(
        'Advanced Payment',
        places=2,
        validators=[Optional(), NumberRange(min=0)],
        default=0,
        render_kw={'placeholder': 'e.g. 3000.00'}
    )
    hourly_rate      = DecimalField(
        'Hourly Rate (hourly only)',
        places=2,
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'placeholder': 'e.g. 120.00'}
    )
    estimated_hours  = IntegerField(
        'Estimated Hours (hourly only)',
        validators=[Optional(), NumberRange(min=0)]
    )
    stages           = FieldList(
        FormField(PricingStageForm),
        min_entries=1
    )
    submit           = SubmitField('Save Proposal')


#
#  NEW: Change‐Request & Share Link Forms
#

class ChangeRequestForm(FlaskForm):
    """Client writes a one‐line change request on their dashboard."""
    message = StringField(
        'Change Request',
        validators=[DataRequired(), Length(max=500)],
        render_kw={'placeholder': 'Describe the change you’d like…'}
    )
    submit  = SubmitField('Send Change Request')


class ShareLinkForm(FlaskForm):
    """Flipper to create / deactivate a client‐share link."""
    active  = BooleanField('Share this project dashboard with client')
    submit  = SubmitField('Save Sharing Setting')
