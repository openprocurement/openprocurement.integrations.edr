.. _tutorial:

Tutorial
========

Basic request
-------------

In order to get information from EDR by code EDRPOU you need to make a request to `api/1.0/verify` endpoint, passing code as GET parameter:

.. include:: tutorial/basic_request.http
   :code:
Response consists of the following fields: `x_edrInternalId`, `registrationStatusDetails`, `registrationStatus`, `identification.schema`, `identification.id`, `identification.legalName`, `identification.url`.

* `x_edrInternalId` - unique identification of the subject,
* `registrationStatusDetails` - text state of the entity (uk),
* `registrationStatus` - text state of the entity,
* `identification.schema` - “UA-EDR”
* `identification.id` - EDRPOU; if the subject - an individual entrepreneur - instead of IPN system returns ten zeros, because the data is confidential,
* `identification.legalName` -  name of the entity,
* `identification.url` - link to the entity with detailed information.

Also response contains `meta.sourceDate` field - date when information from EDR API was received.

Request with Individual Tax Number
----------------------------------

If you need to obtain information about individual entrepreneurs then send a request with code IPN:

.. include:: tutorial/ipn.http
   :code:

Errors
------
Response to the unsuccessful request contains list of errors  with description, code in response body and status.

API returns the following response when limit of requests to the resource is reached:

.. include:: tutorial/too_many_requests.http
   :code:
Response contains message with time when current limitation will expire.

When given EDRPOU (IPN) were not found in EDR response will contains message `EDRPOU not found`:

.. include:: tutorial/empty_response.http
   :code:

When GET parameter  `code` or `passport` is not passed proxy-server will return response with error:

.. include:: tutorial/without_param.http
   :code:

Rest of errors appears on the proxy-server side and can contain one of next messages:

.. include:: tutorial/invalid_token.http
   :code:
or

.. include:: tutorial/payment_requests.http
   :code:

These errors are not related to the created request.

File-reference
------
There are another endpoint `/details/x_edrInternalId` to process request to EDR to get detailed information using
parameter `x_edrInternalId`, received in first response. Only user from group `robot` have permissions to process
given request. Request looks like:

.. include:: tutorial/details.http
   :code:

File-reference name is `edr_identification.yaml` and is uploaded to tenders with status ` active.pre-qualification` and
`procurementMethodType: aboveThresholdEU, competitiveDialogueUA, competitiveDialogueEU` and tender with status
`active.qualification` with `procurementMethodType: aboveThresholdUA, aboveThresholdUA.defense,
aboveThresholdEU, competitiveDialogueUA.stage2, competitiveDialogueEU.stage2`. Field `identifier.scheme` should have
value `UA-EDR`. File-reference is uploaded to `award/qualification` with `pending` status and contains field
`documentType: registerExtract`. If `identifier:id` is not found in EDR, then file will include next error
`{error: {code: notFound, errorDetails: Couldn't find this code in EDR.}}`.

File-reference also includes service information in `meta`.

* `author` - author of file-reference, have value `IdentificationBot`,
* `id` - unique identifier of file-reference,
* `sourceDate` - creation date,
* `sourceRequests` - list of request numbers to `API`, `EDR-proxy`,
* `version` - file-reference format version.

Value `meta.version` now have value 1.1.1. First number - major version (delete field, rename, remove), second number -
minor version (add field), third number - bugfix version (changes that do not change fields, but fix bugs).
For example, changing of file-reference name from `edr_request.yaml` to `edr_identification.yaml` increased
first number(major version), adding `meta.author` field increased second number (minor version).