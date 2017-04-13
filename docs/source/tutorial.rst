.. _tutorial:

Tutorial
========

Basic request
-------------

In order to get information from EDR by code EDRPOU you need to make a request to `api/1.0/verify` endpoint, passing code as GET parameter:

.. include:: tutorial/basic_request.http
   :code:
Response consists of the following fields: `x_edrInternalId`, `state.registrationStatusDetails`, `state.registrationStatus`, `identification.schema`, `identification.id`, `identification.legalName`, `identification.url`.

* `x_edrInternalId` - unique identification of the subject,
* `state.registrationStatusDetails` - text state of the entity (uk),
* `state.registrationStatus` - text state of the entity,
* `identification.schema` - “UA-EDR”
* `identification.id` - EDRPOU; if the subject - an individual entrepreneur - instead of IPN system returns ten zeros, because the data is confidential,
* `identification.legalName` -  name of the entity,
* `identification.url` - link to the entity with detailed information.

Request with Individual Tax Number
----------------------------------

If you need to obtain information about individual entrepreneurs then send a request with code IPN:

.. include:: tutorial/ipn.http
   :code:

Errors
------
Response to the unsuccessful request contains list of errors  with description and code in response body and status `403 Forbidden`.

API returns the following response when limit of requests to the resource is reached:

.. include:: tutorial/too_many_requests.http
   :code:
Response contains message with time when current limitation will be expired.

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