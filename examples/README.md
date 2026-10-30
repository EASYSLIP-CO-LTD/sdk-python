# Examples

Each script runs one operation. Run it with `--help` to see its inputs.
Set `EASYSLIP_API_KEY_FILE` to a private file containing your API key, then run:

```sh
python examples/get_info.py --run
python examples/verify_bank_by_payload.py --input input.json --run
```

The input file contains operation arguments, such as `{"payload":"your slip payload"}`.
Use `image` for a local image path, `image_url` for a public image URL,
`account_id` for a receiving account, and `job_id` for a submitted job.
Async submissions accept `callback_url`.

`--run` confirms that you intend to make a request. Verification can consume quota,
and account examples can change your receiving accounts. Results are printed to
your terminal and may contain personal data. Keep the API key out of input files
and logs. Custom API URLs use `EASYSLIP_V1_BASE_URL` and `EASYSLIP_V2_BASE_URL`.
